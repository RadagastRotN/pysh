from .generator import make_source


from .main import *

#
#
# @make_pipe
# def filter(gen, threshold=0):
#     yield from (x for x in gen if x > threshold)
#
#
# # for x in filter([1, -1, 2, 3], 1):
# #     print(x)
#
#

#
#
# @make_drain
# def wc(source):
#     return sum(1 for _ in source)
#
#
# print(cat_list([1, 2, 3, 4]) | wc())
#
#
# print(pwd())
# with cd("Rozwój/materialy/Popiel/NOPE"):
#     print(pwd())
#     with open("artykuły") as infile:
#         print(infile.read())
# print(pwd())

# cat_list([1,2]) | file_saver("/tmp/test", "a")

# for x in [1,2] + cat_list([3,4]):
#     print(x)

# print(wc("/home/radagast/Rozwój/memorado", Flags.L))
# print(cat_list("1 1 3 4 5a".split()) | wc())


# print(du("/home/radagast/Rozwój/memorado"))
# print("---")
# print(du("/home/radagast/Rozwój/decyzje"))

# for x in cat_list("aaaa babab cdcd".split()) | sed('y', 'abcd', 'XYZŹ'):
#     print(x)

# for x in cat_list("3 a\t2 c\t 1b".split('\t')) | sort(Flags.G):
#     print(x)

# for x in cat_list("3 K\t2 M\t 1G".split('\t')) | sort(Flags.H):
#     print(x)

# find(".", name=re.compile(".*\.py")) | echo()

# print(cat_list("a b c d efgh\t1 x".split(" ")) | wc())

print(list(find("/tmp/pysh_test", name=r"test.*")))


# @make_source(lambda a, b: b - a)
# def foo(a, b):
#     yield from range(a, b)
#
#
# f = foo(10, 15)
# print(f)
# print(len(f))
# print(*f)
