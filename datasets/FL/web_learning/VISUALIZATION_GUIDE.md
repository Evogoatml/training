# Heap Sort Visualization Guide

## 🎨 Visualization Features

This project includes **two amazing visualization modes** for heap sort:

### 1. ✨ Animated Visualization

**What it does:**
- Automatically plays through all heap sort steps
- Beautiful color-coded animations
- Shows array bars, heap tree, and statistics simultaneously
- Smooth transitions between steps

**Features:**
- 📊 **Array Bars**: Visual representation of the array
  - Height = value
  - Colors indicate state (unsorted/sorted/swapping)
  - Numbers displayed on top of bars
  
- 🌳 **Heap Tree**: Tree structure showing:
  - Parent-child relationships
  - Node values
  - Current operation highlights
  
- 📈 **Statistics Panel**: Real-time metrics
  - Current step number
  - Operation type
  - Comparisons and swaps count

**Usage:**
```python
from heap_visualizer import visualize_heap_sort

arr = [64, 34, 25, 12, 22, 11, 90]
visualize_heap_sort(arr, mode='animated', delay=0.8)
```

**Parameters:**
- `mode='animated'`: Automatic playback
- `delay`: Time per step in seconds (0.4-1.5 recommended)

---

### 2. 🎮 Interactive Visualization

**What it does:**
- Keyboard-controlled step-by-step viewing
- Navigate at your own pace
- Perfect for detailed study

**Keyboard Controls:**
- **→** or **SPACE**: Next step
- **←**: Previous step  
- **Home**: Jump to first step
- **End**: Jump to last step
- **ESC**: Close window

**Features:**
- All features of animated mode
- Full control over progression
- Detailed step information
- Can go back to review previous steps

**Usage:**
```python
from heap_visualizer import visualize_heap_sort

arr = [64, 34, 25, 12, 22, 11, 90]
visualize_heap_sort(arr, mode='interactive')
```

---

## 🎯 Visual Elements Explained

### Colors
- 🔵 **Blue (Default)**: Normal array elements
- 🟢 **Green (Sorted)**: Elements in their final sorted positions
- 🟠 **Orange (Swapping)**: Elements currently being swapped
- 🔴 **Red (Comparing)**: Elements being compared during heapify

### Array Visualization
- **Bar height** = Element value
- **Bar color** = Current state
- **Index numbers** = Position in array
- **Value labels** = Number on top of each bar

### Heap Tree
- **Circles** = Tree nodes (array elements)
- **Lines** = Parent-child relationships
- **Root node** = Top of tree (index 0)
- **Leaf nodes** = Bottom nodes with no children

---

## 📊 What Each Operation Shows

### 1. Build Start
- Shows initial array
- "Building Max Heap..." message

### 2. Heapify
- Highlights node being heapified
- Shows tree structure
- Shows comparisons being made

### 3. Heap Built
- Complete max heap structure
- All nodes in heap order

### 4. Swap
- Highlights two elements being swapped
- Shows before/after in tree
- Updates array visualization

### 5. Extract
- Root moved to sorted portion
- Heap size decreases
- New root is heapified

### 6. Complete
- All elements sorted
- Green bars throughout
- "Sorting Complete!" message

---

## 💡 Tips for Best Experience

1. **Start Small**: Use 5-7 elements to see every detail
2. **Adjust Speed**: Faster for overview, slower for learning
3. **Use Interactive Mode**: For detailed step-by-step study
4. **Try Different Arrays**: See how different inputs behave
5. **Watch the Tree**: Heap tree shows the data structure clearly

---

## 🔧 Customization

### Change Colors
Edit `heap_visualizer.py` and modify the `colors` dictionary:
```python
self.colors = {
    'default': '#3498db',    # Your color
    'comparing': '#e74c3c',   # Your color
    # ... etc
}
```

### Adjust Animation Speed
```python
visualize_heap_sort(arr, mode='animated', delay=0.4)  # Fast
visualize_heap_sort(arr, mode='animated', delay=1.5)  # Slow
```

### Change Window Size
Edit the `figsize` parameter in the visualizer classes:
```python
self.fig = plt.figure(figsize=(16, 10))  # Width x Height
```

---

## 🎓 Educational Use

Perfect for:
- Understanding heap sort algorithm
- Visualizing data structure operations
- Learning binary heap properties
- Studying O(n log n) sorting
- Teaching computer science concepts

---

Enjoy the beautiful visualizations! 🚀

