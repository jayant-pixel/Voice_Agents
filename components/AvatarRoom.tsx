"use client";

import {
    RoomAudioRenderer,
    VideoTrack,
    useTracks,
    isTrackReference,
    TrackToggle,
    DisconnectButton,
    useLocalParticipantPermissions,
    useConnectionState,
    useDataChannel,
    useLocalParticipant,
    useRoomContext,
} from "@livekit/components-react";
import { ConnectionState, Track, RpcInvocationData } from "livekit-client";
import { useMemo, useCallback, useState, useEffect } from "react";
import { ManufacturingOverlay, OverlayData } from "./ManufacturingOverlay";

export function AvatarRoom() {
    const room = useRoomContext();
    const connectionState = useConnectionState();
    const { localParticipant } = useLocalParticipant();
    const [overlay, setOverlay] = useState<OverlayData | null>(null);

    const tracks = useTracks(
        [{ source: Track.Source.Camera, withPlaceholder: false }],
        { onlySubscribed: false }
    );

    // ... (lines 20-130 roughly)



    const avatarTrack = useMemo(() => {
        return tracks
            .filter(isTrackReference)
            .find(
                (track) =>
                    track.participant?.attributes?.agentType === "avatar" ||
                    track.participant?.identity?.includes("avatar")
            );
    }, [tracks]);

    const permissions = useLocalParticipantPermissions();
    const canPublishAudio = permissions?.canPublish ?? true;

    // Show loading screen if not fully connected OR avatar isn't here yet
    const isLoading = connectionState !== ConnectionState.Connected || !avatarTrack;

    // Register RPC methods for overlay control
    useEffect(() => {
        if (!room) return;

        // Handler for showing overlay
        const handleShowOverlay = async (data: RpcInvocationData) => {
            try {
                const parsed = JSON.parse(data.payload) as OverlayData;
                setOverlay(parsed);
                return JSON.stringify({ success: true });
            } catch (error) {
                console.error("Failed to parse overlay data:", error);
                return JSON.stringify({ success: false, error: "Invalid payload" });
            }
        };

        // Handler for hiding overlay
        const handleHideOverlay = async () => {
            setOverlay(null);
            return JSON.stringify({ success: true });
        };

        // Register methods on the ROOM instance (not localParticipant)
        room.registerRpcMethod("showOverlay", handleShowOverlay);
        room.registerRpcMethod("hideOverlay", handleHideOverlay);

        // Cleanup on unmount
        return () => {
            room.unregisterRpcMethod("showOverlay");
            room.unregisterRpcMethod("hideOverlay");
        };
    }, [room]);

    useDataChannel(
        "lk.transcription",
        useCallback(() => {
            /* ignore LiveKit transcription payloads to avoid noisy console warnings */
        }, [])
    );

    const handleDismissOverlay = useCallback(() => {
        setOverlay(null);
    }, []);

    return (
        <div className="relative w-full h-[100dvh] bg-black overflow-hidden flex flex-col items-center justify-center">
            {/* LOADING OVERLAY - Triggered by connection signals */}
            {isLoading && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black text-white px-6 text-center">
                    <div className="flex flex-col items-center gap-8 max-w-sm">
                        {/* Animated Industrial Dithered Box */}
                        <div className="relative w-16 h-16 border-4 border-white shadow-[8px_8px_0px_0px_#FF0055]">
                            <div className="absolute inset-0 bg-[#FF0055] animate-pulse"></div>
                        </div>

                        <div className="space-y-3">
                            <h2 className="text-3xl font-mono uppercase tracking-[0.3em] font-black italic">
                                {connectionState === ConnectionState.Connecting ? "SYNCING..." : "CONNECTING..."}
                            </h2>
                            <p className="text-sm font-secondary italic opacity-70 tracking-tight">
                                Please wait while we establish a secure link with Cara.
                            </p>
                        </div>

                        {/* Connection Status Pips */}
                        <div className="flex gap-4">
                            <div className={`h-1 w-10 ${connectionState === ConnectionState.Connecting || connectionState === ConnectionState.Connected ? 'bg-[#FF0055]' : 'bg-white/10'}`}></div>
                            <div className={`h-1 w-10 ${connectionState === ConnectionState.Connected ? 'bg-[#FF0055]' : 'bg-white/10'}`}></div>
                            <div className={`h-1 w-10 ${avatarTrack ? 'bg-[#FF0055]' : 'bg-white/10'}`}></div>
                        </div>
                    </div>
                </div>
            )}

            {/* Avatar Video - Full Screen with Enhancement Filters */}
            {avatarTrack && (
                <VideoTrack
                    trackRef={avatarTrack}
                    className="w-full h-full object-cover"
                    style={{
                        transform: 'scale(1.01)',
                        filter: 'contrast(1.1) saturate(1.2)'
                    }}
                />
            )}

            {/* Overlay Card - Right Side Container */}
            <div className="absolute inset-0 z-30 flex items-center justify-end p-6 pointer-events-none">
                <div className="pointer-events-auto max-w-md w-full">
                    <ManufacturingOverlay overlay={overlay} onDismiss={handleDismissOverlay} />
                </div>
            </div>

            {/* Minimalist Control Bar Overlay */}
            {!isLoading && (
                <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-40">
                    <div className="flex bg-white border-4 border-black shadow-[8px_8px_0px_0px_#000] p-1">
                        <TrackToggle
                            source={Track.Source.Microphone}
                            showIcon={false}
                            disabled={!canPublishAudio}
                            className="custom-room-button px-10 py-4 font-mono text-base font-black uppercase tracking-widest !bg-white !text-black !border-none hover:!bg-black hover:!text-white transition-all transform active:translate-y-1 active:shadow-none"
                        >
                            Mic
                        </TrackToggle>
                        <div className="w-[4px] bg-black"></div>
                        <DisconnectButton
                            className="custom-room-button px-10 py-4 font-mono text-base font-black uppercase tracking-widest !bg-white !text-black !border-none hover:!bg-[#FF0055] hover:!text-white transition-all transform active:translate-y-1 active:shadow-none"
                        >
                            End
                        </DisconnectButton>
                    </div>
                </div>
            )}

            <RoomAudioRenderer />
        </div>
    );
}

