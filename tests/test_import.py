import os

project_dir = os.path.dirname(os.path.dirname(__file__))
package_dir = os.path.join(project_dir, "src", "nisyscfg")

# Walk all module directories and create import tests for all non-private
# Python modules.
for root, dirs, files in os.walk(package_dir):
    relative_root = os.path.relpath(root, os.path.join(project_dir, "src"))
    base_name = ".".join(relative_root.split(os.path.sep))
    if "__init__.py" in files:
        exec("def test_{}(): import {}".format(base_name.replace(".", "_"), base_name))
    for f in files:
        if f.endswith(".py") and not f.startswith("_"):
            mod_name = base_name + "." + f[:-3]
            exec("def test_{}(): import {}".format(mod_name.replace(".", "_"), mod_name))
