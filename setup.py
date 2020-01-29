from setuptools import find_packages, setup

setup(
    name="merkle-drop",
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "click",
        "web3",
        "contract-deploy-tools",
        "eth_utils",
        "flask",
        "flask_cors",
        "pendulum",
        "gunicorn",
    ],
    entry_points="""
    [console_scripts]
    merkle-drop=merkle_drop.cli:main
    """,
)
