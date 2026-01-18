"use client";

import { PreJoin, LiveKitRoom } from "@livekit/components-react";
import { useRouter } from "next/navigation";
import { useState, useCallback, useRef } from "react";
import { AvatarRoom } from "@/components/AvatarRoom";

export default function Home() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [roomName, setRoomName] = useState<string | null>(null);
  const joiningRef = useRef(false);

  const handleJoin = useCallback(async (values: { username: string }) => {
    // Prevent multiple simultaneous join requests
    if (joiningRef.current) {
      console.log("Join already in progress, skipping duplicate request");
      return;
    }
    joiningRef.current = true;

    const room = "cara-room";
    setRoomName(room);
    try {
      const resp = await fetch(`/api/token?room=${room}&username=${values.username}`);
      const data = await resp.json();
      if (data.token) {
        setToken(data.token);

        // REQUEST AGENT (Lifecycle Start)
        fetch("/api/livekit/request-agent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ room }),
        }).catch(err => console.error("Failed to request agent:", err));

      } else {
        console.error("No token received", data);
        joiningRef.current = false;
      }
    } catch (e) {
      console.error("Error fetching token:", e);
      joiningRef.current = false;
    }
  }, []);

  const handleDisconnect = useCallback(async () => {
    if (roomName) {
      // STOP AGENT (Lifecycle End)
      fetch(`/api/livekit/stop-agent?room-name=${encodeURIComponent(roomName)}`, {
        method: "DELETE",
      }).catch(err => console.error("Failed to stop agent:", err));
    }
    setToken(null);
    setRoomName(null);
    joiningRef.current = false;
  }, [roomName]);

  return (
    <div className="agent-component-wrapper">
      {/* FULL SCREEN ROOM OVERLAY */}
      {token && (
        <div className="fixed inset-0 z-[100] bg-black">
          <LiveKitRoom
            token={token}
            serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={handleDisconnect}
          >
            <AvatarRoom />
          </LiveKitRoom>
        </div>
      )}

      {/* The Window Frame (PreJoin State) */}
      <div className="agent-box is-tabs">
        {/* Window Header (Top Bar) */}
        <div className="win__title hudson">
          <div className="support-design-box bn">
            <div className="media-wrap">
              <div className="win-dot is-square"></div>
              <p className="text-size-tiny text-type-raster">SAY HI CARA</p>
            </div>
          </div>
        </div>

        <div className="agent-interface-flex">
          {/* LEFT SIDEBAR */}
          <div className="agent-box-wrap hudson">
            {/* Logo Area */}
            <div className="hudson-bar">
              <div className="mb-8">{/* Spacer */}</div>
              <div className="recent-wrap"></div>
            </div>

            {/* Content */}
            <div className="tab-short-wrap">
              <div className="text-size-large font-secondary">
                <em>So basically</em>
              </div>
              <div className="tab-short-lines">
                <svg width="100%" height="5" viewBox="0 0 130 5" fill="none">
                  <line y1="2.5" x2="130" y2="2.5" stroke="black" strokeOpacity="0.2" strokeWidth="1" strokeDasharray="2 2" />
                </svg>
              </div>
              <p className="text-size-tiny">
                I'm kind of like the older sister you never had. Let's talk about whatever's on your mind. I'll be here.
              </p>
            </div>

            <div className="conversation-wrap">
              <div className="text-size-large font-secondary">
                <em>Integrations</em>
              </div>
              <div className="tab-short-lines">
                <svg width="100%" height="5" viewBox="0 0 473 5" fill="none">
                  <line y1="2.5" x2="473" y2="2.5" stroke="black" strokeOpacity="0.2" strokeWidth="1" strokeDasharray="2 2" />
                </svg>
              </div>

              <div className="conversation-grid">
                <div className="conversation-content">
                  <p className="home-tabs-heading-text">EMAIL</p>
                  <p className="home-tabs-text text-size-tiny">Inbox zero, finally.</p>
                </div>
                <div className="conversation-content">
                  <p className="home-tabs-heading-text">CALENDAR</p>
                  <p className="home-tabs-text text-size-tiny">Scheduling made sane.</p>
                </div>
                <div className="conversation-content">
                  <p className="home-tabs-heading-text">TODO</p>
                  <p className="home-tabs-text text-size-tiny">Tasks, managed.</p>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT CONTENT AREA */}
          <div className="tabs-content-wrapper">
            <div className="hudson-video-wrap">
              {/* Persona Static Image as Background */}
              <img
                src="https://lab.anam.ai/persona_thumbnails/cara_windowsofa.png"
                alt="Cara"
                className="persona-image"
              />

              {/* PreJoin Component - overlaid on the image */}
              <div className="prejoin-overlay">
                <PreJoin
                  onSubmit={handleJoin}
                  defaults={{
                    videoEnabled: false,
                    audioEnabled: true,
                  }}
                  persistUserChoices={true}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
