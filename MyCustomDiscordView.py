from discord.errors import HTTPException
from discord.ui import View


class MyGenericView(View):
    """
    Generic Custom Discord View that handles:
        1. An interaction check to make sure only the author can interact with the component
        2. Auto disables every component on timeout
    """
    def __init__(self, timeout, author):
        super().__init__(timeout=timeout)
        self.author = author

    async def interaction_check(self, interaction):
        if interaction.user == self.author:
            return True
        return False

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self._internal_update_view()

    async def _internal_update_view(self):
        try:
            await self.message.edit(content="Out of time :boom:", view=self)
        except HTTPException:
            pass
