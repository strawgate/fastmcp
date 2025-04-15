from src.fastmcp import FastMCP

mcp = FastMCP()

class Sample:
    def __init__(self, name):
        self.name = name

    @mcp.tool(delay_registration=True)
    def first_tool(self):
        """First tool description."""
        return f"Executed first tool {self.name}."
    
    @mcp.tool(delay_registration=True)
    def second_tool(self):
        """Second tool description."""
        return f"Executed second tool {self.name}."
    
first_sample = Sample("First")
second_sample = Sample("Second")

mcp.perform_delayed_registration("first", first_sample)
mcp.perform_delayed_registration("second", second_sample)

def main():
    mcp.run("sse")

if __name__ == "__main__":
    main()