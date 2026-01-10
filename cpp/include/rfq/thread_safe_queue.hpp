#pragma once

#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <optional>
#include <chrono>
#include <stdexcept>

namespace rfq {

/**
 * ThreadSafeQueue - Lock-free queue for high-throughput RFQ processing
 *
 * Demonstrates:
 * - std::mutex and std::lock_guard for thread safety
 * - std::condition_variable for efficient waiting
 * - std::atomic for lock-free operations
 * - Move semantics for efficiency
 * - Template metaprogramming
 *
 * Suitable for high-frequency trading scenarios where multiple threads
 * produce and consume RFQ messages.
 */
template<typename T>
class ThreadSafeQueue {
public:
    ThreadSafeQueue()
        : shutdown_(false)
        , size_(0) {}

    ~ThreadSafeQueue() {
        shutdown();
    }

    // Non-copyable
    ThreadSafeQueue(const ThreadSafeQueue&) = delete;
    ThreadSafeQueue& operator=(const ThreadSafeQueue&) = delete;

    // Movable
    ThreadSafeQueue(ThreadSafeQueue&& other) noexcept {
        std::lock_guard<std::mutex> lock(other.mutex_);
        queue_ = std::move(other.queue_);
        shutdown_.store(other.shutdown_.load());
        size_.store(other.size_.load());
    }

    ThreadSafeQueue& operator=(ThreadSafeQueue&& other) noexcept {
        if (this != &other) {
            std::scoped_lock lock(mutex_, other.mutex_);
            queue_ = std::move(other.queue_);
            shutdown_.store(other.shutdown_.load());
            size_.store(other.size_.load());
        }
        return *this;
    }

    /**
     * Push an item onto the queue (copy)
     */
    void push(const T& item) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (shutdown_.load(std::memory_order_acquire)) {
                throw std::runtime_error("Queue is shut down");
            }
            queue_.push(item);
            size_.fetch_add(1, std::memory_order_release);
        }
        cv_.notify_one();
    }

    /**
     * Push an item onto the queue (move)
     */
    void push(T&& item) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (shutdown_.load(std::memory_order_acquire)) {
                throw std::runtime_error("Queue is shut down");
            }
            queue_.push(std::move(item));
            size_.fetch_add(1, std::memory_order_release);
        }
        cv_.notify_one();
    }

    /**
     * Emplace construct item in queue (perfect forwarding)
     */
    template<typename... Args>
    void emplace(Args&&... args) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (shutdown_.load(std::memory_order_acquire)) {
                throw std::runtime_error("Queue is shut down");
            }
            queue_.emplace(std::forward<Args>(args)...);
            size_.fetch_add(1, std::memory_order_release);
        }
        cv_.notify_one();
    }

    /**
     * Try to pop an item (non-blocking)
     * Returns std::nullopt if queue is empty
     */
    std::optional<T> tryPop() {
        std::lock_guard<std::mutex> lock(mutex_);

        if (queue_.empty()) {
            return std::nullopt;
        }

        T item = std::move(queue_.front());
        queue_.pop();
        size_.fetch_sub(1, std::memory_order_release);

        return item;
    }

    /**
     * Pop an item (blocking until available)
     * Returns std::nullopt if queue is shut down
     */
    std::optional<T> pop() {
        std::unique_lock<std::mutex> lock(mutex_);

        cv_.wait(lock, [this] {
            return !queue_.empty() || shutdown_.load(std::memory_order_acquire);
        });

        if (shutdown_.load(std::memory_order_acquire) && queue_.empty()) {
            return std::nullopt;
        }

        T item = std::move(queue_.front());
        queue_.pop();
        size_.fetch_sub(1, std::memory_order_release);

        return item;
    }

    /**
     * Pop an item with timeout
     * Returns std::nullopt if timeout or shutdown
     */
    template<typename Rep, typename Period>
    std::optional<T> popFor(const std::chrono::duration<Rep, Period>& timeout) {
        std::unique_lock<std::mutex> lock(mutex_);

        bool success = cv_.wait_for(lock, timeout, [this] {
            return !queue_.empty() || shutdown_.load(std::memory_order_acquire);
        });

        if (!success || (shutdown_.load(std::memory_order_acquire) && queue_.empty())) {
            return std::nullopt;
        }

        T item = std::move(queue_.front());
        queue_.pop();
        size_.fetch_sub(1, std::memory_order_release);

        return item;
    }

    /**
     * Check if queue is empty (lock-free)
     */
    bool empty() const noexcept {
        return size_.load(std::memory_order_acquire) == 0;
    }

    /**
     * Get queue size (lock-free)
     */
    size_t size() const noexcept {
        return size_.load(std::memory_order_acquire);
    }

    /**
     * Clear all items from queue
     */
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        std::queue<T> empty_queue;
        queue_.swap(empty_queue);
        size_.store(0, std::memory_order_release);
    }

    /**
     * Shutdown queue (wake up all waiting threads)
     */
    void shutdown() {
        shutdown_.store(true, std::memory_order_release);
        cv_.notify_all();
    }

    /**
     * Check if queue is shutdown
     */
    bool isShutdown() const noexcept {
        return shutdown_.load(std::memory_order_acquire);
    }

    /**
     * Restart queue after shutdown
     */
    void restart() {
        shutdown_.store(false, std::memory_order_release);
    }

private:
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic<bool> shutdown_;
    std::atomic<size_t> size_;
};

/**
 * BoundedThreadSafeQueue - Queue with maximum capacity
 *
 * Useful for backpressure in high-frequency scenarios
 */
template<typename T>
class BoundedThreadSafeQueue {
public:
    explicit BoundedThreadSafeQueue(size_t max_size)
        : max_size_(max_size)
        , shutdown_(false)
        , size_(0) {}

    ~BoundedThreadSafeQueue() {
        shutdown();
    }

    // Non-copyable, movable
    BoundedThreadSafeQueue(const BoundedThreadSafeQueue&) = delete;
    BoundedThreadSafeQueue& operator=(const BoundedThreadSafeQueue&) = delete;
    BoundedThreadSafeQueue(BoundedThreadSafeQueue&&) noexcept = default;
    BoundedThreadSafeQueue& operator=(BoundedThreadSafeQueue&&) noexcept = default;

    /**
     * Try to push (returns false if full)
     */
    bool tryPush(T&& item) {
        std::unique_lock<std::mutex> lock(mutex_);

        if (queue_.size() >= max_size_) {
            return false;
        }

        if (shutdown_.load(std::memory_order_acquire)) {
            throw std::runtime_error("Queue is shut down");
        }

        queue_.push(std::move(item));
        size_.fetch_add(1, std::memory_order_release);
        cv_not_empty_.notify_one();

        return true;
    }

    /**
     * Push with blocking (waits if full)
     */
    void push(T&& item) {
        std::unique_lock<std::mutex> lock(mutex_);

        cv_not_full_.wait(lock, [this] {
            return queue_.size() < max_size_ ||
                   shutdown_.load(std::memory_order_acquire);
        });

        if (shutdown_.load(std::memory_order_acquire)) {
            throw std::runtime_error("Queue is shut down");
        }

        queue_.push(std::move(item));
        size_.fetch_add(1, std::memory_order_release);
        cv_not_empty_.notify_one();
    }

    /**
     * Pop with blocking
     */
    std::optional<T> pop() {
        std::unique_lock<std::mutex> lock(mutex_);

        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty() || shutdown_.load(std::memory_order_acquire);
        });

        if (shutdown_.load(std::memory_order_acquire) && queue_.empty()) {
            return std::nullopt;
        }

        T item = std::move(queue_.front());
        queue_.pop();
        size_.fetch_sub(1, std::memory_order_release);
        cv_not_full_.notify_one();

        return item;
    }

    size_t size() const noexcept {
        return size_.load(std::memory_order_acquire);
    }

    size_t maxSize() const noexcept {
        return max_size_;
    }

    bool empty() const noexcept {
        return size_.load(std::memory_order_acquire) == 0;
    }

    bool full() const noexcept {
        return size_.load(std::memory_order_acquire) >= max_size_;
    }

    void shutdown() {
        shutdown_.store(true, std::memory_order_release);
        cv_not_empty_.notify_all();
        cv_not_full_.notify_all();
    }

private:
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    std::condition_variable cv_not_empty_;
    std::condition_variable cv_not_full_;
    const size_t max_size_;
    std::atomic<bool> shutdown_;
    std::atomic<size_t> size_;
};

} // namespace rfq
