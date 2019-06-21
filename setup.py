from setuptools import setup, find_packages

setup(
    name="merkle-drop",
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    packages=find_packages(),
    install_requires=["click", "eth_utils", "eth-hash[pycryptodome]", "pendulum"],
    entry_points="""
    [console_scripts]
    merkle-drop=merkle_drop.cli:main
    """,
)
