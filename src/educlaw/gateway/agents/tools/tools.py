
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, fn):
        self.tools[name] = fn 

    async def execute(self, name, args):
        if name not in self.tools:
            return f"Tool {name} not found"
        return await self.tools[name](args)
    
async def add_tool(args):
    return args["a"] + args["b"]

def create_default_tools():
    registry = ToolRegistry()
    registry.register("add", add_tool)
    return registry