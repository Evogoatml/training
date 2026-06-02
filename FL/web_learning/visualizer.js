/**
 * Visualization Engine
 * Handles all animations and visual representations
 */

class HeapVisualizer {
    constructor(heapInstance) {
        this.heap = heapInstance;
        this.arrayCanvas = document.getElementById('arrayCanvas');
        this.treeCanvas = document.getElementById('treeCanvas');
        // arrayCanvas may have been removed from the DOM (we allow tree-only view).
        // If it's missing, create an offscreen canvas so code that expects a context doesn't crash,
        // and mark that array canvas is not in DOM so drawing can be skipped.
        if (!this.arrayCanvas) {
            this._arrayCanvasInDom = false;
            this.arrayCanvas = document.createElement('canvas');
        } else {
            this._arrayCanvasInDom = true;
        }

        if (!this.treeCanvas) {
            throw new Error('Required DOM element #treeCanvas not found');
        }

        this.arrayCtx = this.arrayCanvas.getContext('2d');
        this.treeCtx = this.treeCanvas.getContext('2d');
        
        // Animation state
        this.animationSpeed = 5;
        this.isPlaying = false;
        this.currentAnimationStep = 0;
        this.highlightedIndices = [];
        this.sortedIndices = [];
        this.heapSize = 0;
        
        // Colors
        this.colors = {
            default: '#6366f1',
            sorted: '#34d399',
            comparing: '#f87171',
            swapping: '#fbbf24',
            root: '#fbbf24',
            background: '#0f172a',
            text: '#f1f5f9',
            grid: '#475569'
        };

        this.setupCanvases();
    }

    setupCanvases() {
        // Set canvas dimensions
        const updateCanvasSize = () => {
            const arrayWrapper = this.arrayCanvas.parentElement;
            const treeWrapper = this.treeCanvas.parentElement;

            // Keep original fixed-height behavior to match initial UI
            if (this._arrayCanvasInDom && arrayWrapper) {
                this.arrayCanvas.width = Math.max(100, arrayWrapper.clientWidth - 40);
                this.arrayCanvas.height = 400;
            } else {
                // offscreen canvas or removed: set safe defaults
                this.arrayCanvas.width = 400;
                this.arrayCanvas.height = 200;
            }

            if (treeWrapper) {
                this.treeCanvas.width = Math.max(200, treeWrapper.clientWidth - 40);
                // Use computed CSS height to match visual layout (e.g., 280px)
                const cssHeight = window.getComputedStyle(this.treeCanvas).height;
                const h = parseInt(cssHeight, 10) || Math.max(200, treeWrapper.clientHeight - 40);
                this.treeCanvas.height = h;
            }

            this.draw();
        };

        updateCanvasSize();
        window.addEventListener('resize', updateCanvasSize);
    }

    setSpeed(speed) {
        this.animationSpeed = speed;
    }

    draw() {
        if (this._arrayCanvasInDom) {
            this.drawArray();
        }
        this.drawTree();
    }

    drawArray() {
        const ctx = this.arrayCtx;
        const canvas = this.arrayCanvas;
        const heap = this.heap.getHeap();
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.fillStyle = this.colors.background;
        ctx.fillRect(0, 0, width, height);

        if (heap.length === 0) {
            ctx.fillStyle = this.colors.text;
            ctx.font = '24px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('Heap is empty', width / 2, height / 2);
            return;
        }

        const barWidth = Math.max(30, (width - 40) / heap.length - 10);
        const maxValue = Math.max(...heap, 1);
        const barHeightScale = (height - 80) / maxValue;

        // Draw grid lines
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
            const y = 20 + (height - 40) * (i / 5);
            ctx.beginPath();
            ctx.moveTo(20, y);
            ctx.lineTo(width - 20, y);
            ctx.stroke();
        }

        // Draw bars
        for (let i = 0; i < heap.length; i++) {
            const x = 20 + i * (barWidth + 10);
            const barHeight = heap[i] * barHeightScale;
            const y = height - 30 - barHeight;

            // Determine color
            let color = this.colors.default;
            if (this.sortedIndices.includes(i)) {
                color = this.colors.sorted;
            } else if (this.highlightedIndices.includes(i) && this.swappingMode) {
                color = this.colors.swapping;
            } else if (this.highlightedIndices.includes(i)) {
                color = this.colors.comparing;
            } else if (i >= this.heapSize && this.heapSize > 0) {
                color = this.colors.sorted;
            }

            // Draw bar
            ctx.fillStyle = color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = color;
            ctx.fillRect(x, y, barWidth, barHeight);
            ctx.shadowBlur = 0;

            // Draw border
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.strokeRect(x, y, barWidth, barHeight);

            // Draw value
            ctx.fillStyle = 'white';
            ctx.font = 'bold 14px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(heap[i], x + barWidth / 2, y - 5);

            // Draw index
            ctx.fillStyle = this.colors.text;
            ctx.font = '12px Inter';
            ctx.fillText(i, x + barWidth / 2, height - 10);
        }
    }

    drawTree() {
        const ctx = this.treeCtx;
        const canvas = this.treeCanvas;
        const heap = this.heap.getHeap();
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.fillStyle = this.colors.background;
        ctx.fillRect(0, 0, width, height);

        if (heap.length === 0) {
            ctx.fillStyle = this.colors.text;
            ctx.font = '24px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('Heap is empty', width / 2, height / 2);
            return;
        }

        const heapSize = this.heapSize || heap.length;
        const nodeRadius = 25;
        const nodePositions = this.calculateTreePositions(heap, heapSize, width, height);

        // Draw edges first
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 2;
        for (const [index, pos] of Object.entries(nodePositions)) {
            const idx = parseInt(index);
            const left = 2 * idx + 1;
            const right = 2 * idx + 2;

            if (left < heapSize && nodePositions[left]) {
                this.drawEdge(ctx, pos, nodePositions[left]);
            }
            if (right < heapSize && nodePositions[right]) {
                this.drawEdge(ctx, pos, nodePositions[right]);
            }
        }

        // Draw nodes
        for (const [index, pos] of Object.entries(nodePositions)) {
            const idx = parseInt(index);
            let color = this.colors.default;

            if (idx === 0) {
                color = this.colors.root;
            } else if (this.highlightedIndices.includes(idx) && this.swappingMode) {
                color = this.colors.swapping;
            } else if (this.highlightedIndices.includes(idx)) {
                color = this.colors.comparing;
            }

            this.drawNode(ctx, pos.x, pos.y, nodeRadius, heap[idx], color);
        }
    }

    calculateTreePositions(heap, heapSize, width, height) {
        const positions = {};
        const levels = Math.ceil(Math.log2(heapSize + 1));
        const levelHeight = (height - 100) / levels;
        const startY = 50;

        // BFS to calculate positions
        const queue = [{ index: 0, level: 0, left: 0, right: width }];
        
        while (queue.length > 0) {
            const { index, level, left, right } = queue.shift();
            if (index >= heapSize) continue;

            const x = (left + right) / 2;
            const y = startY + level * levelHeight;

            positions[index] = { x, y };

            // Add children to queue
            const leftChild = 2 * index + 1;
            const rightChild = 2 * index + 2;

            if (leftChild < heapSize) {
                queue.push({
                    index: leftChild,
                    level: level + 1,
                    left: left,
                    right: x
                });
            }

            if (rightChild < heapSize) {
                queue.push({
                    index: rightChild,
                    level: level + 1,
                    left: x,
                    right: right
                });
            }
        }

        return positions;
    }

    drawEdge(ctx, from, to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
    }

    drawNode(ctx, x, y, radius, value, color) {
        // Draw circle
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Draw border
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Draw value
        ctx.fillStyle = 'white';
        ctx.font = 'bold 16px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(value, x, y);
    }

    highlight(indices, isSwapping = false) {
        this.highlightedIndices = indices;
        this.swappingMode = isSwapping;
        this.draw();
    }

    setHeapSize(size) {
        this.heapSize = size;
        this.draw();
    }

    setSortedIndices(indices) {
        this.sortedIndices = indices;
        this.draw();
    }

    clearHighlights() {
        this.highlightedIndices = [];
        this.sortedIndices = [];
        this.heapSize = 0;
        this.swappingMode = false;
        this.draw();
    }

    updateArrayDisplay(heap) {
        const display = document.getElementById('arrayDisplay');
        display.innerHTML = '';

        heap.forEach((value, index) => {
            const item = document.createElement('div');
            item.className = 'array-item';
            item.textContent = value;
            
            if (this.sortedIndices.includes(index)) {
                item.classList.add('sorted');
            } else if (this.highlightedIndices.includes(index) && this.swappingMode) {
                item.classList.add('swapping');
            } else if (this.highlightedIndices.includes(index)) {
                item.classList.add('comparing');
            } else if (index === 0) {
                item.classList.add('root');
            }

            display.appendChild(item);
        });
    }
}
