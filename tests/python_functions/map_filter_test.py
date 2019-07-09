

# map
def map_func(x):
    return x * x


list1 = [1, 7, 9, 45, 3]
list2 = list(map(map_func, list1))
print(list2)

# map with lambda
squares = list(map(lambda x: x * x, [0, 1, 2, 3, 4]))
print(squares)


# filter
def filter_func(x):
    return x > 10


list3 = list(filter(filter_func, list2))
print(list3)
