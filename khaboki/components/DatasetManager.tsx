"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Download, Database, BarChart3 } from "lucide-react";
import { DatasetStats } from "@/types";

export function DatasetManager() {
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:5000/dataset/stats");
      console.log(response)
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching dataset stats:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const exportDataset = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(
        "http://127.0.0.1:5000/dataset/export?format=json"
      );
      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `khabo_ki_dataset_${
        new Date().toISOString().split("T")[0]
      }.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error exporting dataset:", error);
    } finally {
      setIsExporting(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database size={20} />
          Dataset Management
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          onClick={fetchStats}
          variant="outline"
          className="w-full"
          disabled={isLoading}
        >
          <BarChart3 size={16} className="mr-2" />
          {isLoading ? "Loading..." : "Refresh Stats"}
        </Button>

        {stats && (
          <div className="text-sm space-y-2 p-3 bg-gray-50 rounded-md">
            <p>
              <strong>Total Restaurants:</strong> {stats.total_restaurants}
            </p>
            <div>
              <strong>Platforms:</strong>
              <ul className="ml-4 mt-1">
                {Object.entries(stats.platform_breakdown).map(
                  ([platform, count]) => (
                    <li key={platform}>
                      • {platform}: {count}
                    </li>
                  )
                )}
              </ul>
            </div>
            <p>
              <strong>Last Updated:</strong>{" "}
              {new Date(stats.last_updated).toLocaleString()}
            </p>
          </div>
        )}

        <Button
          onClick={exportDataset}
          disabled={isExporting}
          className="w-full"
        >
          <Download size={16} className="mr-2" />
          {isExporting ? "Exporting..." : "Export Dataset"}
        </Button>
      </CardContent>
    </Card>
  );
}