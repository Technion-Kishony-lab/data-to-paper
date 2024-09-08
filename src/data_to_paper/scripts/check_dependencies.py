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
    print("Checking for required tools...")
    check_tool_installed('pdflatex')
    check_tool_installed('pandoc')


def main():
    check_dependencies()


if __name__ == "__main__":
    main()
