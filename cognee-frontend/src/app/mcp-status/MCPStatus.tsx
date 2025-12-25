"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BackIcon } from "@/ui/Icons";
import { StatusDot } from "@/ui/elements";
import Header from "@/ui/Layout/Header";
import { useAuthenticatedUser } from "@/modules/auth";
import fetch from "@/utils/fetch";

interface MCPStatusInfo {
  healthy: boolean;
  mcpUrl: string;
  lastChecked: string;
  error?: string;
  transportMode?: string;
  apiUrl?: string;
}

export default function MCPStatus() {
  const { user } = useAuthenticatedUser();
  const [status, setStatus] = useState<MCPStatusInfo>({
    healthy: false,
    mcpUrl: process.env.NEXT_PUBLIC_MCP_API_URL || "http://localhost:9000",
    lastChecked: new Date().toISOString(),
  });
  const [loading, setLoading] = useState(true);

  const checkMCPStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch.checkMCPHealth();
      const data = await response.json();
      
      setStatus({
        healthy: response.ok,
        mcpUrl: process.env.NEXT_PUBLIC_MCP_API_URL || "http://localhost:9000",
        lastChecked: new Date().toISOString(),
        transportMode: data.transport_mode || data.transportMode || "N/A",
        apiUrl: data.api_url || data.apiUrl || "N/A",
      });
    } catch (error) {
      setStatus({
        healthy: false,
        mcpUrl: process.env.NEXT_PUBLIC_MCP_API_URL || "http://localhost:9000",
        lastChecked: new Date().toISOString(),
        error: error instanceof Error ? error.message : "Failed to connect to MCP server",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkMCPStatus();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(checkMCPStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full max-w-[1920px] mx-auto">
      <Header user={user} />

      <div className="relative flex flex-row items-start gap-2.5">
        <Link href="/dashboard" className="flex-1/5 py-4 px-5 flex flex-row items-center gap-5">
          <BackIcon />
          <span>back</span>
        </Link>
        
        <div className="flex-1/5 flex flex-col gap-2.5">
          <div className="py-4 px-5 rounded-xl bg-white">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-xl font-semibold">MCP Server Status</h2>
              <StatusDot isActive={status.healthy} />
            </div>
            <div className="text-sm text-gray-400 mb-8">
              Monitor the status of the Model Context Protocol (MCP) server
            </div>

            {loading ? (
              <div className="text-center py-8 text-gray-500">
                Checking MCP server status...
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-gray-500 uppercase mb-1">Status</div>
                    <div className={`font-medium ${status.healthy ? "text-green-600" : "text-red-600"}`}>
                      {status.healthy ? "Connected" : "Disconnected"}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs text-gray-500 uppercase mb-1">MCP URL</div>
                    <div className="font-mono text-sm">{status.mcpUrl}</div>
                  </div>

                  {status.transportMode && (
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Transport Mode</div>
                      <div className="font-medium">{status.transportMode}</div>
                    </div>
                  )}

                  {status.apiUrl && (
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">API URL</div>
                      <div className="font-mono text-sm">{status.apiUrl}</div>
                    </div>
                  )}

                  <div>
                    <div className="text-xs text-gray-500 uppercase mb-1">Last Checked</div>
                    <div className="text-sm">
                      {new Date(status.lastChecked).toLocaleString()}
                    </div>
                  </div>
                </div>

                {status.error && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="text-sm font-semibold text-red-800 mb-1">Error</div>
                    <div className="text-sm text-red-700">{status.error}</div>
                  </div>
                )}

                <div className="mt-6 pt-4 border-t border-gray-200">
                  <button
                    onClick={checkMCPStatus}
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? "Checking..." : "Refresh Status"}
                  </button>
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-xs text-blue-800 font-semibold mb-2">About MCP Server</div>
                  <div className="text-xs text-blue-700">
                    The Model Context Protocol (MCP) server provides a unified interface for AI agents 
                    to interact with Cognee&apos;s memory system. It enables tools for data ingestion, 
                    querying, and knowledge management.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1/5 py-4 px-5 rounded-xl"></div>
        <div className="flex-1/5 py-4 px-5 rounded-xl"></div>
        <div className="flex-1/5 py-4 px-5 rounded-xl"></div>
      </div>
    </div>
  );
}
