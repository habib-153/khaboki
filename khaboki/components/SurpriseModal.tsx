"use client";

import { SurpriseModalProps } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RestaurantCard } from "./RestaurantCard";
import { Button } from "@/components/ui/button";
import { Sparkles, RefreshCw } from "lucide-react";

export function SurpriseModal({
  isOpen,
  onClose,
  restaurant,
  onRefresh,
  isLoading,
  previousCount = 0,
}: SurpriseModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="text-yellow-500" size={20} />
            Surprise Pick for You!
            {previousCount > 0 && (
              <span className="text-sm font-normal text-gray-500">
                (Suggestion #{previousCount})
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
              <span className="ml-2">
                {previousCount > 0
                  ? "Finding another surprise..."
                  : "Finding your surprise..."}
              </span>
            </div>
          ) : restaurant ? (
            <>
              <RestaurantCard
                restaurant={restaurant}
                showCompareButton={false}
              />
              <div className="flex gap-2">
                <Button
                  onClick={onRefresh}
                  variant="outline"
                  className="flex-1"
                  disabled={isLoading}
                >
                  <RefreshCw size={16} className="mr-2" />
                  Try Another
                </Button>
                {/* <Button onClick={onClose} className="flex-1">
                  I&apos;ll Try This!
                </Button> */}
              </div>

              {previousCount > 1 && (
                <div className="text-center">
                  <p className="text-xs text-gray-500">
                    {previousCount} suggestions so far. We&apos;ll avoid repeating
                    previous picks!
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p>No restaurants available for surprise selection.</p>
              <Button onClick={onClose} className="mt-4">
                Close
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}