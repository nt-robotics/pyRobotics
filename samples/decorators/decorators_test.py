# 1
def bread(func):
    def wrapper():
        print("1")
        func()
        print("<\______/>")
    return wrapper


def ingredients(func):
    def wrapper():
        print("#помидоры#")
        func()
        print("~салат~")
    return wrapper


@bread
@ingredients
def sandwich(food="--ветчина--"):
    print(food)


sandwich()


# 2
def a_decorator_passing_arguments(function_to_decorate):
    def a_wrapper_accepting_arguments(arg1, arg2):
        print("Смотри, что я получил:", arg1, arg2)
        function_to_decorate(arg1, arg2)
    return a_wrapper_accepting_arguments

# Теперь, когда мы вызываем функцию, которую возвращает декоратор, мы вызываем её "обёртку",
# передаём ей аргументы и уже в свою очередь она передаёт их декорируемой функции
@a_decorator_passing_arguments
def print_full_name(first_name, last_name):
    print("Меня зовут", first_name, last_name)


print_full_name("Vasya", "Pupkin")