import llvmlite
import llvmlite.binding as llvm

print(f"llvmlite version: {llvmlite.__version__}")
try:
    print(f"Attr: {dir(llvm)}")
    llvm.initialize()
    print("Init 1 success")
    llvm.initialize_native_target()
    print("Init 2 success")
    llvm.initialize_native_asmprinter()
    print("Init 3 success")
    
    methods = [x for x in dir(llvm) if "create" in x]
    print(f"Available create methods: {methods}")

except Exception as e:
    print(f"Fail: {e}")


