from pathlib import Path
from shutil import copytree, ignore_patterns, rmtree
from playwright.sync_api import sync_playwright

# URL = "https://dion.vc/event/vdamirov-ngu"
URL = "https://dion.vc/auth/login/guest?slug=vdamirov-ngu&eventId=efd7ac2a-099e-40f7-97b4-376288385951&referrer=https%3A%2F%2Fdion.vc%2Fevent%2Fvdamirov-ngu"

People = [
    ["Герман Даниил", "24943"]
    ["Даниил Герман", "24943"]
    ["Герман", "24943"]
    ["Даниил", "24943"]
]

# Your real Chrome profile folder on macOS
SOURCE_PROFILE = Path("/Users/danielgehrman/Documents/Programming/Projects/dion-bot/Profile 3")

# Where to place the cloned profiles
CLONES_DIR = Path("./chrome_profile_clones")


def make_fresh_clone(src: Path, dst: Path) -> None:
    if dst.exists():
        rmtree(dst)

    copytree(
        src,
        dst,
        ignore=ignore_patterns(
            "Singleton*",
            "Lock*",
            "*.lock",
            "Crashpad",
            "ShaderCache",
            "GrShaderCache",
            "Code Cache",
            "GPUCache",
            "Safe Browsing",
        ),
    )


def main():
    if not SOURCE_PROFILE.exists():
        raise FileNotFoundError(f"Source profile not found: {SOURCE_PROFILE}")

    CLONES_DIR.mkdir(parents=True, exist_ok=True)

    clone_paths = [CLONES_DIR / f"profile{i}" for i in range(1, 4)]

    print("Make sure Chrome is fully closed before running this.")
    input("Press Enter to clone your Chrome profile...")

    for clone_path in clone_paths:
        make_fresh_clone(SOURCE_PROFILE, clone_path)

    instances = []

    with sync_playwright() as p:
        for i, clone_path in enumerate(clone_paths, start=1):
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(clone_path),
                headless=False,
                channel="chromium",  # uses installed Google Chrome instead of bundled Chromium
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    # "--no-sandbox",         # only if needed on Linux
                    # "--disable-gpu",        # rarely needed anymore
                ],
                ignore_default_args=["--enable-automation"]
            )

            page = context.new_page()
            page.goto(URL)

            instances.append({
                "id": f"worker-{i}",
                "context": context,
                "page": page,
            })

            print(f"Opened instance {i} with profile clone: {clone_path}")

        input("Opened 3 Chrome-based cloned sessions. Press Enter to close...")

        for context in contexts:
            context.close()

def main():
    # get people count

    # load the 

# def main():
#     with sync_playwright() as p:
#         # Launch a single Chromium instance
#         # browser = p.chromium.launch_persistent_context("profile1", headless=False)
#         browser = p.chromium.launch(headless=False)

#         contexts = []
#         pages = []

#         # Create 3 isolated contexts (separate cookies/cache)
#         for i in range(3):
#             context = browser.new_context()
#             page = context.new_page()
#             page.goto(URL)

#             contexts.append(context)
#             pages.append(page)

#         print("Opened 3 isolated sessions. Press Enter to close...")
#         input()

#         browser.close()

if __name__ == "__main__":
    main()