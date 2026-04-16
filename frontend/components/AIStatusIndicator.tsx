"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Wifi, WifiOff, Loader2 } from "lucide-react";

interface AIStatusIndicatorProps {
  apiUrl?: string;
}

export default function AIStatusIndicator({ apiUrl = "http://localhost:8000" }: AIStatusIndicatorProps) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [latency, setLatency] = useState<number | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const start = Date.now();
        const response = await fetch(`${apiUrl}/health`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });
        const end = Date.now();
        
        if (response.ok) {
          setStatus("online");
          setLatency(end - start);
        } else {
          setStatus("offline");
        }
      } catch {
        setStatus("offline");
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const statusConfig = {
    checking: {
      icon: <Loader2 className="w-3 h-3 animate-spin" />,
      color: "text-yellow-400",
      bgColor: "bg-yellow-400/20",
      label: "检测中...",
      pulse: true,
    },
    online: {
      icon: <Wifi className="w-3 h-3" />,
      color: "text-emerald-400",
      bgColor: "bg-emerald-400/20",
      label: latency ? `在线 (${latency}ms)` : "在线",
      pulse: false,
    },
    offline: {
      icon: <WifiOff className="w-3 h-3" />,
      color: "text-red-400",
      bgColor: "bg-red-400/20",
      label: "离线",
      pulse: true,
    },
  };

  const config = statusConfig[status];

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full
        ${config.bgColor} backdrop-blur-sm border border-white/5
      `}
    >
      <div className={`relative ${config.color}`}>
        {config.pulse && (
          <span className="absolute inset-0 rounded-full animate-ping opacity-75">
            <span className={`inline-flex rounded-full h-full w-full ${config.color.replace('text-', 'bg-')} opacity-75`} />
          </span>
        )}
        {config.icon}
      </div>
      <span className={`text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
      <Activity className="w-3 h-3 text-gray-500" />
    </motion.div>
  );
}
