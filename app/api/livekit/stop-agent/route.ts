import { NextRequest, NextResponse } from "next/server";
import { AgentDispatchClient } from "livekit-server-sdk";

export async function DELETE(request: NextRequest) {
    return handleStop(request);
}

export async function POST(request: NextRequest) {
    return handleStop(request);
}

async function handleStop(request: NextRequest) {
    try {
        const roomName = request.nextUrl.searchParams.get("room-name");
        const agentName = process.env.LIVEKIT_AGENT_NAME || "surens-avatar";

        if (!roomName) {
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

        const serverUrl = NEXT_PUBLIC_LIVEKIT_URL.replace("wss://", "https://");

        const agentDispatchClient = new AgentDispatchClient(
            serverUrl,
            LIVEKIT_API_KEY,
            LIVEKIT_API_SECRET
        );

        const dispatches = await agentDispatchClient.listDispatch(roomName);
        const dispatch = dispatches.find((candidate) => {
            if (candidate.agentName !== agentName) return false;
            const deletedAt = candidate.state?.deletedAt;
            if (deletedAt === undefined) return true;
            if (typeof deletedAt === "bigint") {
                return Number(deletedAt) === 0;
            }
            return deletedAt === 0;
        });

        if (!dispatch) {
            return NextResponse.json({
                success: true,
                message: "No active agent dispatch for this room",
            });
        }

        try {
            await agentDispatchClient.deleteDispatch(dispatch.id, roomName);
        } catch (err) {
            if (err instanceof Error && (err as { code?: string }).code === "not_found") {
                return NextResponse.json({
                    success: true,
                    message: "Agent dispatch already removed",
                });
            }
            throw err;
        }

        return NextResponse.json({
            success: true,
            message: "Agent dispatch has been deleted for the room",
        });
    } catch (error) {
        console.error("Error stopping agent:", error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : "Unknown error" },
            { status: 500 }
        );
    }
}
