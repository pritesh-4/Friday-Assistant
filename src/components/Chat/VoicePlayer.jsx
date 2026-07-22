import { useState, useRef, useEffect } from "react";
import { Play, Pause, Trash2, RotateCcw, Volume2 } from "lucide-react";

/**
 * Format time in seconds to MM:SS string format.
 * @param {number} seconds
 * @returns {string}
 */
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export default function VoicePlayer({
  audioUrl,
  duration = 0,
  onDelete,
  onReRecord
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(duration);

  const audioRef = useRef(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setAudioDuration(audio.duration);
      }
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [audioUrl]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().catch((err) => console.error("Playback error:", err));
      setIsPlaying(true);
    }
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    if (!audio || !audioDuration) return;

    const seekTime = (parseFloat(e.target.value) / 100) * audioDuration;
    audio.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const progressPercentage = audioDuration > 0 ? (currentTime / audioDuration) * 100 : 0;

  return (
    <div className="w-full flex items-center justify-between gap-3 p-3 rounded-xl bg-[#141414] border border-[#00f0ff]/20 shadow-[0_0_15px_rgba(0,240,255,0.05)]">
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Play/Pause toggle */}
      <button
        type="button"
        onClick={togglePlayPause}
        className="w-9 h-9 rounded-lg bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] border border-[#00f0ff]/30 flex items-center justify-center transition-all cursor-pointer shrink-0"
        title={isPlaying ? "Pause audio" : "Play audio"}
      >
        {isPlaying ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
      </button>

      {/* Audio Wave / Progress track */}
      <div className="flex-1 flex flex-col gap-1 min-w-0">
        <div className="flex items-center justify-between text-[10px] font-mono text-on-surface-variant">
          <span className="flex items-center gap-1 text-[#00f0ff]">
            <Volume2 size={11} /> Recorded Audio
          </span>
          <span>
            {formatTime(currentTime)} / {formatTime(audioDuration || duration)}
          </span>
        </div>

        <div className="relative w-full h-1.5 bg-white/10 rounded-full overflow-hidden flex items-center">
          <div
            className="h-full bg-gradient-to-r from-[#00f0ff] to-[#d1bcff] transition-all duration-100"
            style={{ width: `${progressPercentage}%` }}
          />
          <input
            type="range"
            min="0"
            max="100"
            value={progressPercentage || 0}
            onChange={handleSeek}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
          />
        </div>
      </div>

      {/* Control Actions: Re-record & Delete */}
      <div className="flex items-center gap-1 shrink-0">
        {onReRecord && (
          <button
            type="button"
            onClick={onReRecord}
            className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors cursor-pointer"
            title="Re-record audio"
          >
            <RotateCcw size={14} />
          </button>
        )}

        {onDelete && (
          <button
            type="button"
            onClick={onDelete}
            className="p-2 rounded-lg text-on-surface-variant hover:text-[#ffb4ab] hover:bg-white/5 transition-colors cursor-pointer"
            title="Delete recording"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
