# Min Heap Implementation in Python

class MinHeap:
    def __init__(self) -> None:
        """
        On this implementation the heap list is initialized with a value
        """
        self.heap_list: list[tuple[int,]] = [0]
        self.current_size = 0

    def _sift_up(self, i: int) -> None:
        """
        Moves the value up in the tree to maintain the heap property.
        """
        # While the element is not the root or the left element
        parent = i // 2
        while parent > 0:
            # If the element is less than its parent swap the elements
            if self.heap_list[i][0] < self.heap_list[parent][0]:
                self.heap_list[i], self.heap_list[parent] = self.heap_list[parent], self.heap_list[i]
            else:
                break
            # Move the index to the parent to keep the properties
            i = parent
            parent = i // 2

    def push(self, value: int, elem = None) -> None:
        """
        Inserts a value into the heap
        """
        # Append the element to the heap
        self.heap_list.append((value, elem))
        # Increase the size of the heap.
        self.current_size += 1
        # Move the element to its position from bottom to the top
        self._sift_up(self.current_size)

    def _sift_down(self, i: int) -> None:
        # If the current node has at least one child
        while i * 2 <= self.current_size:
            # Get the index of the min child of the current node
            mc = self._min_child(i)
            # Swap the values of the current element if its greater than its min child
            if self.heap_list[i][0] > self.heap_list[mc][0]:
                self.heap_list[i], self.heap_list[mc] = self.heap_list[mc], self.heap_list[i]
            i = mc

    def _min_child(self, i: int) -> None:
        # If the current node has only one child, return the index of the unique child
        child1 = i * 2
        child2 = child1 + 1
        if child2 > self.current_size:
            return child1
        else:
            # Here in the current node has two children
            # Return the index of the min child according to their values
            if self.heap_list[child1][0] < self.heap_list[child2][0]:
                return child1
            else:
                return child2

    def pop(self) -> tuple[int,]:
        # Equal to 1 since the heap list was initialized with a value
        if len(self.heap_list) == 1:
            return None

        # Get root of the heap (The min value of the heap)
        root = self.heap_list[1]

        # Move the last value of the heap to the root
        self.heap_list[1] = self.heap_list.pop()

        # Decrease the size of the heap
        self.current_size -= 1

        # Move down the root (value at index 1) to keep the heap property
        self._sift_down(1)

        # Return the min value of the heap
        return root
