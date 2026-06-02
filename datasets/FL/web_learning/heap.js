/**
 * Heap Sort Implementation
 * Complete implementation of Max Heap with all DSA operations
 */

class MaxHeap {
    constructor() {
        this.heap = [];
        this.comparisons = 0;
        this.swaps = 0;
        this.animationSteps = [];
        this.currentStep = 0;
        this.isAnimating = false;
    }

    // Clear animation steps before new operation
    clearAnimationSteps() {
        this.animationSteps = [];
        this.currentStep = 0;
    }

    // Get parent index
    parent(index) {
        return Math.floor((index - 1) / 2);
    }

    // Get left child index
    leftChild(index) {
        return 2 * index + 1;
    }

    // Get right child index
    rightChild(index) {
        return 2 * index + 2;
    }

    // Swap two elements
    swap(i, j) {
        [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]];
        this.swaps++;
        
        this.addAnimationStep('swap', {
            indices: [i, j],
            heap: [...this.heap],
            message: `Swapped ${this.heap[j]} and ${this.heap[i]}`
        });
    }

    // Add animation step
    addAnimationStep(type, data) {
        this.animationSteps.push({
            type: type,
            ...data,
            comparisons: this.comparisons,
            swaps: this.swaps,
            timestamp: Date.now()
        });
    }

    // Heapify up (for insert)
    heapifyUp(index) {
        while (index > 0) {
            const parentIdx = this.parent(index);
            this.comparisons++;
            
            this.addAnimationStep('compare', {
                indices: [index, parentIdx],
                heap: [...this.heap],
                message: `Comparing ${this.heap[index]} with parent ${this.heap[parentIdx]}`
            });

            if (this.heap[index] > this.heap[parentIdx]) {
                this.swap(index, parentIdx);
                index = parentIdx;
            } else {
                break;
            }
        }
    }

    // Heapify down (for delete and build heap)
    heapifyDown(index, heapSize = null) {
        if (heapSize === null) heapSize = this.heap.length;
        
        while (true) {
            let largest = index;
            const left = this.leftChild(index);
            const right = this.rightChild(index);

            // Compare with left child
            if (left < heapSize) {
                this.comparisons++;
                
                this.addAnimationStep('compare', {
                    indices: [index, left],
                    heap: [...this.heap],
                    heapSize: heapSize,
                    message: `Comparing ${this.heap[index]} with left child ${this.heap[left]}`
                });

                if (this.heap[left] > this.heap[largest]) {
                    largest = left;
                }
            }

            // Compare with right child
            if (right < heapSize) {
                this.comparisons++;
                
                this.addAnimationStep('compare', {
                    indices: [index, right],
                    heap: [...this.heap],
                    heapSize: heapSize,
                    message: `Comparing ${this.heap[largest]} with right child ${this.heap[right]}`
                });

                if (this.heap[right] > this.heap[largest]) {
                    largest = right;
                }
            }

            if (largest !== index) {
                this.swap(index, largest);
                index = largest;
            } else {
                break;
            }
        }
    }

    // Insert operation
    insert(value) {
        if (value === null || value === undefined) return false;
        
        this.heap.push(value);
        
        this.addAnimationStep('insert', {
            value: value,
            heap: [...this.heap],
            message: `Inserted ${value}`
        });

        this.heapifyUp(this.heap.length - 1);
        
        this.addAnimationStep('heapify_complete', {
            heap: [...this.heap],
            message: 'Heap property restored'
        });

        return true;
    }

    // Delete root (extract max)
    delete() {
        if (this.heap.length === 0) {
            this.addAnimationStep('error', {
                message: 'Heap is empty!'
            });
            return null;
        }

        if (this.heap.length === 1) {
            const value = this.heap.pop();
            this.addAnimationStep('delete', {
                value: value,
                heap: [],
                message: `Deleted root: ${value}`
            });
            return value;
        }

        const root = this.heap[0];
        this.heap[0] = this.heap[this.heap.length - 1];
        this.heap.pop();

        this.addAnimationStep('delete', {
            value: root,
            heap: [...this.heap],
            message: `Deleted root: ${root}, moved last element to root`
        });

        this.heapifyDown(0);
        
        this.addAnimationStep('heapify_complete', {
            heap: [...this.heap],
            message: 'Heap property restored'
        });

        return root;
    }

    // Build max heap from array
    buildHeap(array) {
        this.heap = [...array];
        this.comparisons = 0;
        this.swaps = 0;
        this.animationSteps = [];

        if (this.heap.length === 0) return;

        this.addAnimationStep('build_start', {
            heap: [...this.heap],
            message: 'Starting to build max heap...'
        });

        // Start from last non-leaf node
        const lastNonLeaf = Math.floor((this.heap.length - 2) / 2);

        for (let i = lastNonLeaf; i >= 0; i--) {
            this.addAnimationStep('heapify', {
                index: i,
                heap: [...this.heap],
                message: `Heapifying at index ${i}`
            });

            this.heapifyDown(i);
        }

        this.addAnimationStep('build_complete', {
            heap: [...this.heap],
            message: 'Max heap built successfully!'
        });
    }

    // Heap Sort
    heapSort(array = null) {
        if (array !== null) {
            this.buildHeap(array);
        }

        if (this.heap.length === 0) return [];

        const sortedArray = [];
        const originalHeap = [...this.heap];
        let heapSize = this.heap.length;

        this.addAnimationStep('sort_start', {
            heap: [...this.heap],
            sortedArray: [],
            heapSize: heapSize,
            message: 'Starting heap sort...'
        });

        for (let i = this.heap.length - 1; i >= 0; i--) {
            // Swap root with last element
            this.swaps++;
            [this.heap[0], this.heap[i]] = [this.heap[i], this.heap[0]];

            this.addAnimationStep('extract', {
                extracted: this.heap[i],
                heap: [...this.heap],
                sortedArray: [...sortedArray],
                heapSize: i,
                message: `Extracted ${this.heap[i]} to sorted array`
            });

            sortedArray.unshift(this.heap[i]);
            heapSize--;

            // Heapify the reduced heap
            if (heapSize > 0) {
                this.heapifyDown(0, heapSize);
            }
        }

        // Restore original heap
        this.heap = originalHeap;

        this.addAnimationStep('sort_complete', {
            sortedArray: sortedArray,
            heap: originalHeap,
            message: 'Heap sort completed!'
        });

        return sortedArray;
    }

    // Get heap as array
    getHeap() {
        return [...this.heap];
    }

    // Get root (max element)
    getRoot() {
        return this.heap.length > 0 ? this.heap[0] : null;
    }

    // Get size
    getSize() {
        return this.heap.length;
    }

    // Check if heap is empty
    isEmpty() {
        return this.heap.length === 0;
    }

    // Clear heap
    clear() {
        this.heap = [];
        this.comparisons = 0;
        this.swaps = 0;
        this.animationSteps = [];
        this.currentStep = 0;
    }

    // Get statistics
    getStats() {
        return {
            size: this.heap.length,
            comparisons: this.comparisons,
            swaps: this.swaps,
            steps: this.animationSteps.length
        };
    }

    // Reset statistics
    resetStats() {
        this.comparisons = 0;
        this.swaps = 0;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MaxHeap;
}

