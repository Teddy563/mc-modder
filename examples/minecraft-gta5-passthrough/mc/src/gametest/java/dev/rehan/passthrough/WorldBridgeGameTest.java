package dev.rehan.passthrough;

import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.block.Blocks;

/** Server GameTests for the host's ground: no host needed, WorldBridge is driven directly. */
public class WorldBridgeGameTest {
	/**
	 * A ground column {x, z, yBottom, yTop} becomes barriers, but only where there was air; "clear" removes our
	 * barriers and leaves the player's own blocks (here a stone in the middle of the column) alone.
	 */
	@GameTest(maxTicks = 100)
	public void groundColumnThenClear(final GameTestHelper helper) {
		BlockPos bottom = new BlockPos(2, 1, 2);
		BlockPos middle = bottom.above(1);
		BlockPos top = bottom.above(2);
		BlockPos above = bottom.above(3);
		BlockPos a = helper.absolutePos(bottom);
		helper.setBlock(middle, Blocks.STONE);
		helper.assertTrue(WorldBridge.ready(), "WorldBridge isn't attached to the GameTest server");

		helper.startSequence()
			.thenExecute(() -> WorldBridge.solid(new int[] {a.getX(), a.getZ(), a.getY(), a.getY() + 2}))
			.thenWaitUntil(() -> {
				helper.assertBlockPresent(Blocks.BARRIER, bottom);
				helper.assertBlockPresent(Blocks.STONE, middle);
				helper.assertBlockPresent(Blocks.BARRIER, top);
				helper.assertBlockPresent(Blocks.AIR, above);
			})
			.thenExecute(WorldBridge::clearSolid)
			.thenWaitUntil(() -> {
				helper.assertBlockPresent(Blocks.AIR, bottom);
				helper.assertBlockPresent(Blocks.STONE, middle);
				helper.assertBlockPresent(Blocks.AIR, top);
			})
			.thenSucceed();
	}
}
