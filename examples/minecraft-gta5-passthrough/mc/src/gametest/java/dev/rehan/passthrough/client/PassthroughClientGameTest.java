package dev.rehan.passthrough.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.rehan.passthrough.Passthrough;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
import java.net.URI;
import java.util.Locale;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

/**
 * The host's side of the bridge, played by the test: connect to HostLink, read the hello, drive the camera with
 * "cam" messages, send ground and clear, screenshot, and on Windows check the shared-memory frame header.
 * Runs with -Dpassthrough.noAutoWorld=true (set by the clientGameTest run), so the mod leaves world creation to us.
 */
@SuppressWarnings("UnstableApiUsage")
public class PassthroughClientGameTest implements FabricClientGameTest {
	private static final int TIMEOUT_TICKS = 400;

	@Override
	public void runTest(final ClientGameTestContext context) {
		try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
			singleplayer.getConnection().waitForChunksRender();
			context.takeScreenshot("passthrough-no-host");

			Host host = new Host(Integer.getInteger("passthrough.port", 25599));
			ScheduledExecutorService camLoop = Executors.newSingleThreadScheduledExecutor();
			try {
				check(host.connectBlocking(10, TimeUnit.SECONDS), "couldn't connect to HostLink");
				JsonObject hello = JsonParser.parseString(host.next()).getAsJsonObject();
				check("hello".equals(hello.get("t").getAsString()), "first message isn't hello: " + hello);
				check(hello.get("v").getAsInt() == 1, "hello version: " + hello);
				check(FrameExporter.NAME.equals(hello.get("shm").getAsString()), "hello shm name: " + hello);
				check(hello.get("pid").getAsLong() == ProcessHandle.current().pid(), "hello pid: " + hello);

				// the host camera where the player's eyes already are, looking a little down: the scene doesn't move
				Vec3 eye = context.computeOnClient(mc -> mc.player.getEyePosition());
				AtomicLong frame = new AtomicLong();
				// a pose older than 2 s counts as no host, so keep sending like a host does (20 Hz is plenty)
				camLoop.scheduleAtFixedRate(() -> host.send(String.format(Locale.ROOT,
					"{\"t\":\"cam\",\"f\":%d,\"p\":[%.3f,%.3f,%.3f],\"r\":[0,30,0],\"fov\":70,\"fp\":true}",
					frame.incrementAndGet(), eye.x, eye.y, eye.z)), 0, 50, TimeUnit.MILLISECONDS);
				context.waitFor(mc -> Passthrough.active, TIMEOUT_TICKS);

				// ground: a 2-high barrier column 3 blocks off, above the eyes (air there in the flat test world)
				BlockPos at = BlockPos.containing(eye.x + 3, eye.y + 2, eye.z + 3);
				host.send(String.format(Locale.ROOT, "{\"t\":\"ground\",\"c\":[%d,%d,%d,%d]}", at.getX(), at.getZ(), at.getY(), at.getY() + 1));
				singleplayer.getServer().waitFor(server -> server.overworld().getBlockState(at).is(Blocks.BARRIER)
					&& server.overworld().getBlockState(at.above(1)).is(Blocks.BARRIER), TIMEOUT_TICKS);
				host.send("{\"t\":\"clear\"}");
				singleplayer.getServer().waitFor(server -> server.overworld().getBlockState(at).isAir()
					&& server.overworld().getBlockState(at.above(1)).isAir(), TIMEOUT_TICKS);

				singleplayer.getConnection().waitForChunksRender();
				context.waitTicks(20);
				// on Windows this is the overlay layer only (the world layer went to shared memory and was cleared)
				context.takeScreenshot("passthrough-host-attached");

				if (System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("win")) {
					checkSharedMemory(context);
				}
			} catch (InterruptedException e) {
				throw new AssertionError("interrupted", e);
			} finally {
				camLoop.shutdownNow();
				host.close();
			}
		}
	}

	/** The header a host reads (see FrameExporter): magic MCPT, version 1, a published slot whose seq is even. */
	private static void checkSharedMemory(final ClientGameTestContext context) {
		context.waitFor(mc -> FrameExporter.exporting(), TIMEOUT_TICKS);
		MemorySegment m = openHeader();
		ValueLayout.OfInt i32 = ValueLayout.JAVA_INT_UNALIGNED;
		ValueLayout.OfLong i64 = ValueLayout.JAVA_LONG_UNALIGNED;
		context.waitFor(mc -> m.get(i64, 32) > 0 && m.get(i32, 40) >= 0, TIMEOUT_TICKS);
		// read on the client (render) thread, which is the one publishing: never in the middle of a write
		String header = context.computeOnClient(mc -> {
			int slot = m.get(i32, 40);
			long desc = 256 + 128L * slot;
			return String.format(Locale.ROOT, "magic=%08x version=%d slots=%d published=%d latest=%d seq=%d size=%dx%d",
				m.get(i32, 0), m.get(i32, 4), m.get(i32, 12), m.get(i64, 32), slot, m.get(i64, desc), m.get(i32, desc + 24), m.get(i32, desc + 28));
		});
		Passthrough.LOG.info("shared memory header: {}", header);
		int slot = m.get(i32, 40);
		long desc = 256 + 128L * slot;
		check(m.get(i32, 0) == 0x5450434D, "magic isn't MCPT: " + header);
		check(m.get(i32, 4) == 1, "version isn't 1: " + header);
		check(slot >= 0 && slot < m.get(i32, 12), "latest slot out of range: " + header);
		check((context.computeOnClient(mc -> m.get(i64, desc)) & 1L) == 0L, "latest slot's seq is odd (being written): " + header);
		check(m.get(i32, desc + 24) > 0 && m.get(i32, desc + 28) > 0, "latest slot has no size: " + header);
	}

	private static MemorySegment openHeader() {
		try {
			// CreateFileMappingW on an existing name opens it, as the host's OpenFileMapping would
			return SharedMemory.create(FrameExporter.NAME, 4096).segment;
		} catch (Throwable t) {
			throw new AssertionError("couldn't open " + FrameExporter.NAME, t);
		}
	}

	private static void check(final boolean ok, final String message) {
		if (!ok) {
			throw new AssertionError(message);
		}
	}

	/** A minimal host: a WebSocket client that queues what Minecraft sends. */
	private static final class Host extends WebSocketClient {
		private final BlockingQueue<String> received = new LinkedBlockingQueue<>();

		Host(final int port) {
			super(URI.create("ws://127.0.0.1:" + port));
		}

		String next() throws InterruptedException {
			String message = this.received.poll(10, TimeUnit.SECONDS);
			if (message == null) {
				throw new AssertionError("nothing from HostLink within 10 s");
			}

			return message;
		}

		@Override
		public void onOpen(final ServerHandshake handshake) {
		}

		@Override
		public void onMessage(final String message) {
			this.received.add(message);
		}

		@Override
		public void onClose(final int code, final String reason, final boolean remote) {
		}

		@Override
		public void onError(final Exception e) {
			Passthrough.LOG.warn("test host link error", e);
		}
	}
}
