"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  MessageSquare,
  History,
  Settings,
  User,
  Sparkles,
  Plus,
  Mic,
  FileText,
  TrendingUp,
  ChevronRight,
  Clock,
} from "lucide-react";

interface SidebarProps {
  collapsed?: boolean;
}

const navItems = [
  { icon: MessageSquare, label: "直播策划", href: "/workspace" },
  { icon: History, label: "历史记录", href: "/history" },
  { icon: FileText, label: "商业资产", href: "/assets" },
  { icon: TrendingUp, label: "数据复盘", href: "/analytics" },
];

const mockHistory = [
  { id: 1, title: "Cursor AI 编程助手", time: "2小时前", preview: "关于最新版本的功能介绍..." },
  { id: 2, title: "RAG 知识库实战", time: "昨天", preview: "构建企业级知识管理系统..." },
  { id: 3, title: "Ollama 本地部署", time: "3天前", preview: "如何在本地运行大模型..." },
  { id: 4, title: "LangChain 进阶", time: "1周前", preview: "深入理解 Agent 架构..." },
];

export default function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname();
  const [hoveredItem, setHoveredItem] = useState<number | null>(null);

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={`
        fixed left-0 top-0 h-screen flex flex-col
        bg-black/40 backdrop-blur-xl border-r border-white/5
        transition-all duration-300 z-50
        ${collapsed ? "w-16" : "w-64"}
      `}
    >
      {/* Logo Area */}
      <div className="p-4 border-b border-white/5">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-lg gradient-text"
            >
              DeepInsight
            </motion.span>
          )}
        </Link>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <Link
          href="/workspace"
          className={`
            flex items-center gap-3 p-3 rounded-xl
            bg-gradient-to-r from-primary/20 to-accent/20
            border border-primary/30 hover:border-primary/50
            transition-all duration-200 group
            ${collapsed ? "justify-center" : ""}
          `}
        >
          <Plus className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
          {!collapsed && (
            <span className="text-sm font-medium text-primary">新建直播</span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 overflow-y-auto scrollbar-hide">
        <div className="space-y-1">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onMouseEnter={() => setHoveredItem(index)}
                onMouseLeave={() => setHoveredItem(null)}
                className={`
                  flex items-center gap-3 p-3 rounded-xl
                  transition-all duration-200 relative
                  ${isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                  }
                  ${collapsed ? "justify-center" : ""}
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
                  />
                )}
                <item.icon className={`w-5 h-5 ${isActive ? "text-primary" : ""}`} />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-sm font-medium"
                  >
                    {item.label}
                  </motion.span>
                )}
                {collapsed && hoveredItem === index && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="absolute left-full ml-2 px-2 py-1 bg-card rounded-lg text-sm whitespace-nowrap"
                  >
                    {item.label}
                  </motion.div>
                )}
              </Link>
            );
          })}
        </div>

        {/* History Section */}
        {!collapsed && (
          <div className="mt-8">
            <div className="flex items-center gap-2 px-3 mb-3">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                历史记录
              </span>
            </div>
            <div className="space-y-1">
              {mockHistory.map((item) => (
                <button
                  key={item.id}
                  className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors group text-left"
                >
                  <div className="w-8 h-8 rounded-lg bg-card-border flex items-center justify-center">
                    <Mic className="w-4 h-4 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-300 truncate group-hover:text-white">
                      {item.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{item.time}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* User Profile */}
      <div className="p-3 border-t border-white/5">
        <button
          className={`
            w-full flex items-center gap-3 p-3 rounded-xl
            hover:bg-white/5 transition-colors
            ${collapsed ? "justify-center" : ""}
          `}
        >
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0 text-left">
              <p className="text-sm font-medium text-white truncate">Admin</p>
              <p className="text-xs text-gray-500 truncate">Pro Plan</p>
            </div>
          )}
          {!collapsed && (
            <Settings className="w-4 h-4 text-gray-500 hover:text-white transition-colors" />
          )}
        </button>
      </div>
    </motion.aside>
  );
}
