import asyncio
from main import DrissionPageMCP, run_sync

# This is an example of how to use the refactored DrissionPageMCP controller.
# It's meant for testing and demonstration purposes.

async def main():
    """Main function to test the controller."""
    controller = DrissionPageMCP()
    
    print("--- Connecting to browser ---")
    # Connect to a browser on port 9222
    connection_result = await controller.connect_or_open_browser(debug_port=9222)
    print(connection_result)
    
    if not connection_result["success"]:
        print("Could not connect to browser, exiting.")
        return

    print("\n--- Navigating to a page ---")
    nav_result = await controller.get_page("https://www.bing.com")
    print(nav_result)

    print("\n--- Finding elements (all links) ---")
    elements_result = await controller.get_elements("tag:a")
    if elements_result["success"]:
        print(f"Found {len(elements_result['data'])} link elements.")
    else:
        print(elements_result["error"])

    print("\n--- Typing in a search box ---")
    # Note: The locator for Bing's search box is '#sb_form_q'
    input_result = await controller.input_text("#sb_form_q", "DrissionPage")
    print(input_result)

    print("\n--- Pressing Enter ---")
    key_result = await controller.send_key("Enter")
    print(key_result)
    
    print("\n--- Waiting for results to load ---")
    wait_result = await controller.wait(3)
    print(wait_result)

    print("\n--- Taking a screenshot ---")
    screenshot_result = await controller.get_screenshot(as_file_path="bing_search_results.png")
    print(screenshot_result)

    print("\n--- Test finished ---")


if __name__ == "__main__":
    # To run this test, you would typically have the MCP server running elsewhere
    # and call these methods via the MCP protocol.
    # This direct execution is for demonstration.
    # You need a running event loop to execute async functions.
    asyncio.run(main())