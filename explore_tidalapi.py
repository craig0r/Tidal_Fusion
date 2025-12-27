
import tidalapi
import inspect

def explore_module(module):
    print(f"exploring module: {module.__name__}")
    print("=" * 60)
    
    print(f"File: {module.__file__}")

    all_names = dir(module)
    print(f"\nTop level names: {len(all_names)} found")
    
    for name in all_names:
        if name.startswith("_"): continue
        
        val = getattr(module, name)
        print(f"\nName: {name}")
        print(f"  Type: {type(val)}")
        if hasattr(val, '__doc__') and val.__doc__:
             print(f"  Doc: {val.__doc__.splitlines()[0]}")
        
        # If it's a class, list its members
        if inspect.isclass(val):
             print(f"  Members:")
             for m_name, m_val in inspect.getmembers(val):
                 if not m_name.startswith("_"):
                     print(f"    . {m_name}")

if __name__ == "__main__":
    explore_module(tidalapi)
