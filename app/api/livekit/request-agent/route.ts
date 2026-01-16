import { NextRequest, NextResponse } from "next/server";
import {
    AgentDispatchClient,
    RoomServiceClient,
} from "livekit-server-sdk";

const AGENT_METADATA = { requestedBy: "voice-ai-app" };

export async function POST(request: NextRequest) {
    try {
        let room: string | null = null;
        try {
            const body = await request.json();
            room = body?.room;
        } catch (e) {
            // Body might be empty
        }

        // Also try query param for flexibility
        if (!room) {
            room = request.nextUrl.searchParams.get("room");
        }

        if (!room || typeof room !== "string") {
            return NextResponse.json(
                { error: "Room name is required" },
                { status: 400 }
            );
        }

        const { LIVEKIT_API_KEY, LIVEKIT_API_SECRET, NEXT_PUBLIC_LIVEKIT_URL } = process.env;

        if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET || !NEXT_PUBLIC_LIVEKIT_URL) {
            return NextResponse.json(
                { error: "Server configuration is missing" },
                { status: 500 }
            );
        }

        // Convert wss:// to https://
        const serverUrl = NEXT_PUBLIC_LIVEKIT_URL.replace("wss://", "https://");
        const roomName = room;
        const agentName = process.env.LIVEKIT_AGENT_NAME || "surens-avatar";

        const agentDispatchClient = new AgentDispatchClient(
            serverUrl,
            LIVEKIT_API_KEY,
            LIVEKIT_API_SECRET
        );
        const roomServiceClient = new RoomServiceClient(
            serverUrl,
            LIVEKIT_API_KEY,
            LIVEKIT_API_SECRET
        );

        await ensureRoomExists(roomServiceClient, roomName);

        const dispatches = await agentDispatchClient.listDispatch(roomName);
        const existingDispatch = dispatches.find((dispatch) => {
            if (dispatch.agentName !== agentName) return false;
            const deletedAt = dispatch.state?.deletedAt;
            if (deletedAt === undefined) return true;
            if (typeof deletedAt === "bigint") {
                return Number(deletedAt) === 0;
            }
            return deletedAt === 0;
        });

        if (existingDispatch) {
            return NextResponse.json({ success: true, message: "Agent already active" });
        }

        await agentDispatchClient.createDispatch(roomName, agentName, {
            metadata: JSON.stringify(AGENT_METADATA),
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Error requesting agent:", error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : "Unknown error" },
            { status: 500 }
        );
    }
}

async function ensureRoomExists(
    client: RoomServiceClient,
    roomName: string
): Promise<void> {
    try {
        const rooms = await client.listRooms([roomName]);
        if (rooms.some((room) => room.name === roomName)) {
            return;
        }
    } catch (err) {
        const code = (err as { code?: string }).code;
        if (code && code !== "not_found") {
            throw err;
        }
    }

    try {
        await client.createRoom({ name: roomName });
    } catch (err) {
        const code = (err as { code?: string }).code;
        if (code !== "already_exists") {
            throw err;
        }
    }
}
