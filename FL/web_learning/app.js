/**
 * Main Application Controller
 * Handles UI interactions and coordinates heap operations with visualization
 */

class HeapSortApp {
    constructor() {
        this.heap = new MaxHeap();
        this.visualizer = new HeapVisualizer(this.heap);
        
        this.animationInterval = null;
        this.isAnimating = false;
        this.currentStep = 0;
        this.animationSteps = [];

        this.initializeEventListeners();
        this.updateDisplay();
    }

    initializeEventListeners() {
        // Insert button with validation and inline feedback
        const insertInput = document.getElementById('insertValue');
        const insertBtn = document.getElementById('insertBtn');
        if (insertBtn && insertInput) {
            insertBtn.addEventListener('click', () => {
                const raw = insertInput.value;
                const value = raw !== '' ? parseInt(raw, 10) : NaN;
                if (isNaN(value)) {
                    // show inline error
                    insertInput.classList.add('input-error');
                    insertInput.focus();
                    setTimeout(() => insertInput.classList.remove('input-error'), 600);
                    return;
                }

                this.insert(value);
                insertInput.value = '';
            });

            // Insert on Enter key with same validation
            insertInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    insertBtn.click();
                }
            });
        }

        // Delete button
        document.getElementById('deleteBtn').addEventListener('click', () => {
            this.delete();
        });

        // Clear button
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clear();
        });

        // Build heap button
        document.getElementById('buildHeapBtn').addEventListener('click', () => {
            this.buildHeap();
        });

        // Heap sort button
        document.getElementById('heapSortBtn').addEventListener('click', () => {
            this.heapSort();
        });

        // Reset button
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.reset();
        });

        // Animation controls
        document.getElementById('playPauseBtn').addEventListener('click', () => {
            this.togglePlayPause();
        });

        document.getElementById('stepBtn').addEventListener('click', () => {
            this.stepForward();
        });

        document.getElementById('prevStepBtn').addEventListener('click', () => {
            this.stepBackward();
        });

        // Speed slider
        document.getElementById('speedSlider').addEventListener('input', (e) => {
            const speed = parseInt(e.target.value);
            document.getElementById('speedValue').textContent = speed;
            this.visualizer.setSpeed(speed);
        });
    }

    insert(value) {
        // Stop any current animation and start fresh
        if (this.isAnimating) {
            this.stopAnimation();
        }

        this.heap.clearAnimationSteps();
        this.heap.resetStats();
        const ok = this.heap.insert(value);
        this.playAnimation();

        // If insertion succeeded, scroll the combined visualization slightly into view
        if (ok) {
            // Delay a little so layout updates / animation start
            setTimeout(() => {
                const viz = document.querySelector('.viz-combined') || document.querySelector('.visualization-area');
                if (viz) {
                    // scroll so viz is centered in viewport but keep it subtle
                    viz.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } else {
                    // fallback: small page scroll down
                    window.scrollBy({ top: 120, left: 0, behavior: 'smooth' });
                }
            }, 120);
        }

        
    }

    delete() {
        // Stop any current animation and start fresh
        if (this.isAnimating) {
            this.stopAnimation();
        }

        if (this.heap.isEmpty()) {
            alert('Heap is empty!');
            return;
        }

        this.heap.clearAnimationSteps();
        this.heap.resetStats();
        this.heap.delete();
        this.playAnimation();
    }

    clear() {
        // Stop any current animation
        if (this.isAnimating) {
            this.stopAnimation();
        }

        this.heap.clear();
        this.visualizer.clearHighlights();
        this.updateDisplay();
    }

    buildHeap() {
        // Stop any current animation and start fresh
        if (this.isAnimating) {
            this.stopAnimation();
        }

        const currentHeap = this.heap.getHeap();
        if (currentHeap.length === 0) {
            alert('Heap is empty! Please insert some values first.');
            return;
        }

        this.heap.clearAnimationSteps();
        this.heap.resetStats();
        this.heap.buildHeap(currentHeap);
        this.playAnimation();
    }

    heapSort() {
        // Stop any current animation and start fresh
        if (this.isAnimating) {
            this.stopAnimation();
        }

        const currentHeap = this.heap.getHeap();
        if (currentHeap.length === 0) {
            alert('Heap is empty! Please insert some values first.');
            return;
        }

        this.heap.clearAnimationSteps();
        this.heap.resetStats();
        this.heap.heapSort(currentHeap);
        this.playAnimation();
    }

    reset() {
        this.stopAnimation();
        this.heap.clear();
        this.visualizer.clearHighlights();
        this.currentStep = 0;
        this.animationSteps = [];
        this.updateDisplay();
    }

    playAnimation() {
        // Clear any existing animation interval
        if (this.animationInterval) {
            clearTimeout(this.animationInterval);
        }
        
        this.animationSteps = this.heap.animationSteps;
        this.currentStep = 0;
        this.isAnimating = true;
        
        document.getElementById('playPauseBtn').textContent = 'Pause';
        this.playNextStep();
    }

    playNextStep() {
        // Check if we should stop
        if (!this.isAnimating || this.currentStep >= this.animationSteps.length) {
            if (this.currentStep >= this.animationSteps.length) {
                this.animationComplete();
            }
            return;
        }

        const step = this.animationSteps[this.currentStep];
        this.renderStep(step);

        const delay = Math.max(100, (11 - this.visualizer.animationSpeed) * 100);
        
        this.animationInterval = setTimeout(() => {
            if (this.isAnimating && this.currentStep < this.animationSteps.length) {
                this.currentStep++;
                this.playNextStep();
            } else if (this.currentStep >= this.animationSteps.length) {
                this.animationComplete();
            }
        }, delay);
    }

    renderStep(step) {
        const heap = step.heap || this.heap.getHeap();
        
        // Update visualizer based on step type
        switch (step.type) {
            case 'insert':
            case 'delete':
            case 'heapify_complete':
            case 'build_complete':
                this.visualizer.clearHighlights();
                this.visualizer.setHeapSize(heap.length);
                break;

            case 'compare':
                this.visualizer.highlight(step.indices, false);
                this.visualizer.setHeapSize(step.heapSize || heap.length);
                break;

            case 'swap':
                this.visualizer.highlight(step.indices, true);
                this.visualizer.setHeapSize(step.heapSize || heap.length);
                break;

            case 'heapify':
                this.visualizer.highlight([step.index], false);
                this.visualizer.setHeapSize(heap.length);
                break;

            case 'extract':
                this.visualizer.clearHighlights();
                this.visualizer.setHeapSize(step.heapSize);
                this.visualizer.setSortedIndices(
                    Array.from({ length: step.sortedArray.length }, (_, i) => 
                        heap.length - 1 - i
                    )
                );
                break;

            case 'sort_complete':
                this.visualizer.clearHighlights();
                this.visualizer.setSortedIndices(heap.map((_, i) => i));
                break;
        }

        // Update array display
        this.visualizer.updateArrayDisplay(heap);
        
        // Update statistics
        this.updateStats(step);
    }

    updateStats(step) {
        document.getElementById('arraySize').textContent = this.heap.getSize();
        document.getElementById('comparisons').textContent = step.comparisons || 0;
        document.getElementById('swaps').textContent = step.swaps || 0;
        document.getElementById('currentOp').textContent = step.message || 'Ready';
    }

    togglePlayPause() {
        if (this.isAnimating) {
            this.pauseAnimation();
        } else if (this.animationSteps.length > 0) {
            this.resumeAnimation();
        }
    }

    pauseAnimation() {
        this.isAnimating = false;
        if (this.animationInterval) {
            clearTimeout(this.animationInterval);
        }
        document.getElementById('playPauseBtn').textContent = 'Play';
    }

    resumeAnimation() {
        this.isAnimating = true;
        document.getElementById('playPauseBtn').textContent = 'Pause';
        this.playNextStep();
    }

    stepForward() {
        if (this.currentStep < this.animationSteps.length) {
            this.pauseAnimation();
            this.currentStep++;
            this.renderStep(this.animationSteps[this.currentStep - 1]);
        }
    }

    stepBackward() {
        if (this.currentStep > 0) {
            this.pauseAnimation();
            this.currentStep--;
            if (this.currentStep >= 0) {
                this.renderStep(this.animationSteps[this.currentStep]);
            }
        }
    }

    stopAnimation() {
        this.isAnimating = false;
        if (this.animationInterval) {
            clearTimeout(this.animationInterval);
            this.animationInterval = null;
        }
        document.getElementById('playPauseBtn').textContent = 'Play';
    }

    animationComplete() {
        this.isAnimating = false;
        this.animationInterval = null;
        document.getElementById('playPauseBtn').textContent = 'Play';
        this.visualizer.clearHighlights();
        
        // Keep final visualization
        if (this.animationSteps.length > 0) {
            const finalStep = this.animationSteps[this.animationSteps.length - 1];
            if (finalStep && finalStep.type === 'sort_complete') {
                this.visualizer.setSortedIndices(
                    this.heap.getHeap().map((_, i) => i)
                );
            }
        }
    }

    updateDisplay() {
        this.visualizer.draw();
        const heap = this.heap.getHeap();
        this.visualizer.updateArrayDisplay(heap);
        
        const stats = this.heap.getStats();
        document.getElementById('arraySize').textContent = stats.size;
        document.getElementById('comparisons').textContent = stats.comparisons;
        document.getElementById('swaps').textContent = stats.swaps;
        document.getElementById('currentOp').textContent = 'Ready';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Handle intro page
    const introPage = document.getElementById('introPage');
    const mainApp = document.getElementById('mainApp');
    const startBtn = document.getElementById('startBtn');

    startBtn.addEventListener('click', () => {
        // Hide intro page with animation
        introPage.style.opacity = '0';
        introPage.style.transform = 'scale(0.95)';
        introPage.style.transition = 'all 0.5s ease-out';
        
        setTimeout(() => {
            introPage.style.display = 'none';
            mainApp.style.display = 'block';
            mainApp.style.opacity = '0';
            mainApp.style.transform = 'scale(0.95)';
            mainApp.style.transition = 'all 0.5s ease-in';
            
            // Initialize app after showing main interface
            setTimeout(() => {
                mainApp.style.opacity = '1';
                mainApp.style.transform = 'scale(1)';
                window.app = new HeapSortApp();
                // Footer interactivity
                const footer = document.getElementById('appFooter');
                if (footer) {
                    footer.addEventListener('click', () => {
                        alert('Designed by Sangam Paudel (080BCT073)');
                    });
                }
            }, 100);
        }, 500);
    });

    // Also allow Enter key on intro page
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && introPage.style.display !== 'none') {
            startBtn.click();
        }
    });

    // Back button from main app to intro
    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            // Stop any animation if running
            if (window.app && typeof window.app.stopAnimation === 'function') {
                try { window.app.stopAnimation(); } catch (e) { /* ignore */ }
            }

            // Show intro with reverse animation
            const mainApp = document.getElementById('mainApp');
            introPage.style.display = 'block';
            introPage.style.opacity = '0';
            introPage.style.transform = 'scale(0.95)';
            setTimeout(() => {
                introPage.style.opacity = '1';
                introPage.style.transform = 'scale(1)';
            }, 20);

            // Hide main app
            if (mainApp) {
                mainApp.style.opacity = '0';
                mainApp.style.transform = 'scale(0.95)';
                setTimeout(() => { mainApp.style.display = 'none'; }, 300);
            }
        });
    }
});
