import subprocess


def check_tool_installed(tool):
    try:
        subprocess.run([tool, '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{tool} is installed.")
        return True
    except subprocess.CalledProcessError:
        print(f"{tool} is not installed. Please install it to proceed.")
        print(f"For installation instructions, please refer to the INSTALL.md file.")
        return False


def check_dependencies():
    pdflatex_installed = check_tool_installed('pdflatex')
    pandoc_installed = check_tool_installed('pandoc')
    return pdflatex_installed and pandoc_installed


def main():
    check_dependencies()


if __name__ == "__main__":
    main()
