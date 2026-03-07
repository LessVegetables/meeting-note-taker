import asyncio
from pathlib import Path
import random
from shutil import copytree, ignore_patterns, rmtree
from playwright.async_api import async_playwright

"""
todo
- create dion account for development/testing
- add logging
- add requirements.txt
- turn people into a struct/class
- integrate with tg bot
- add sqlite (or json) to keep track of people
- rewrite the logic a bit so that another person via the tg bot (so, not the "manager") can "join" the lecture
- implement "ai manager" that automatically toggles the button 
- add support for different groups (essentially by filtering the instances in def broadcast() by "if person.group == group")

"""


# URL = "https://dion.vc/event/vdamirov-ngu"
URL = "https://dion.vc/auth/login/guest?slug=vdamirov-ngu&eventId=efd7ac2a-099e-40f7-97b4-376288385951&referrer=https%3A%2F%2Fdion.vc%2Fevent%2Fvdamirov-ngu"
# URL = "devURL"

# id, name, groupNumber
people = [
    {"id": 1,   "name":"Герман Даниил", "groupNumber":"24943"},
    {"id": 2,   "name":"Сотников Тихон", "groupNumber":"24943"},
    {"id": 3,   "name":"Колосов Егор", "groupNumber":"24943"},
]

# Your real Chrome profile folder on macOS
SOURCE_PROFILE = Path("/Users/danielgehrman/Documents/Programming/Projects/dion-bot/Profile 3")

# Where to place the cloned profiles
CLONES_DIR = Path("./chrome_profile_clones")

def make_fresh_clone(src: Path, dst: Path) -> None:
    if dst.exists():
        # rmtree(dst)
        print(f"{dst} alredy exists. Leaving it untouched")
        return

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


async def start_instance(person, p, profile_dir: Path, instance_id: str):
    context = await p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
        channel="chromium",  # uses installed Google Chrome instead of bundled Chromium
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            # "--no-sandbox",         # only if needed on Linux
            # "--disable-gpu",        # rarely needed anymore
        ],
        ignore_default_args=["--enable-automation"],

        # Block all permission popups
        permissions=[],  # grant nothing
        geolocation=None,
    )

    page = await context.new_page()
    await page.goto(URL)

    print(f"{instance_id}: opened")

    # Example interaction
    await page.wait_for_load_state("domcontentloaded")
    title = await page.title()
    print(f"{instance_id}: title = {title}")
    # End example

    # Check if the user needs to enter their name
    if await page.is_visible('#userName'):

        # Entering name
        await page.wait_for_selector('#userName')
        await asyncio.sleep(random.uniform(2, 6))

        nameInput = "" + person.get("name") + " " + person.get("groupNumber")

        for char in nameInput:
            await page.locator('#userName').type(char, delay=0)
            await asyncio.sleep(random.uniform(0.05, 0.2))  # random pause after each character


        # Hitting enter
        await asyncio.sleep(random.uniform(0.5, 2.0))
        await page.locator('#userName').press('Enter')

    # todo: also add await page.click('#login-guest-button')

    # Joining the meeting
    await page.wait_for_load_state("domcontentloaded")

    joinName = await page.get_by_test_id('camera-preview-name').inner_text()

    print(f"{instance_id}: joining as: {joinName}")

    await asyncio.sleep(random.uniform(5.0, 15.0))
    await page.click('#connect-to-call')
   
    await page.wait_for_load_state("domcontentloaded")
    print(f"{instance_id}: joined meeting!")

    return context, page, person, instance_id


async def toggle_button(instance):
    context, page, person, instance_id = instance

    personName = person.get("name")

    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(random.uniform(3.0, 9.0))

    print(f"{instance_id}: clicking button...\tName: {personName}")

    if await page.is_visible('#btn-hand-off'):
        await page.click('#btn-hand-off')

        await page.wait_for_selector('#btn-hand-on', state='visible', timeout=10000)
        if await page.is_visible('#btn-hand-on'):
            print(f"{instance_id}: hand is raised!\tName: {personName}")
        else:
            print(f"{instance_id}: ERROR HAND WAS NOT raised ERROR\tName: {personName}")

    elif await page.is_visible('#btn-hand-on'):
        await page.click('#btn-hand-on')

        await page.wait_for_selector('#btn-hand-off', state='visible', timeout=10000)
        if await page.is_visible('#btn-hand-off'):
            print(f"{instance_id}: hand is lowered!\tName: {personName}")
        else:
            print(f"{instance_id}: ERROR HAND WAS NOT LOWERED ERROR\tName: {personName}")
    else:
        print(f"{instance_id}: ERROR TOGGLING BUTTON ERROR\tName: {personName}")


async def broadcast(results, fn):
    await asyncio.gather(*[
        fn(instance) for instance in results
    ])

async def main():
    if not SOURCE_PROFILE.exists():
            raise FileNotFoundError(f"Source profile not found: {SOURCE_PROFILE}")

    CLONES_DIR.mkdir(parents=True, exist_ok=True)

    print("Make sure Chrome is fully closed before running this.")
    input("Press Enter to clone your Chrome profile...")

    # create the profiles (doesn't override existing ones)
    for person in people:
        make_fresh_clone(SOURCE_PROFILE, CLONES_DIR / f"profile{person.get("id")}")


    # "start the engine"
    instances = [] # context, page, person, instance_id

    async with async_playwright() as p:
        results = await asyncio.gather(*[
            start_instance(person, p, CLONES_DIR / f"profile{person.get("id")}", f"instance-{person.get("id")}")
            for person in people
        ])

        while(True):
            command = input("Enter command:")
            match command:
                case "toggle hand":
                    await broadcast(results, toggle_button)
                case "exit":
                    confirmExit = input("Are you sure you want EVERYBODY to leave the meeting?\nHit enter to confirm\n'cancel' to cancel")
                    if confirmExit == "":
                        break

        for context, _page, _, _ in results:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())