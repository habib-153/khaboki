/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";

interface SearchFiltersProps {
  onFilterChange: (filters: any) => void;
}

export function SearchFilters({ onFilterChange }: SearchFiltersProps) {
  const [filters, setFilters] = useState({
    cuisineType: "",
    minRating: 0,
    maxDeliveryTime: 60,
    platforms: ["foodpanda", "ubereats", "pathao"],
  });

  const handleFilterChange = (key: string, value: any) => {
    const updatedFilters = { ...filters, [key]: value };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  const handlePlatformToggle = (platform: string) => {
    const currentPlatforms = [...filters.platforms];
    if (currentPlatforms.includes(platform)) {
      const updatedPlatforms = currentPlatforms.filter((p) => p !== platform);
      handleFilterChange("platforms", updatedPlatforms);
    } else {
      handleFilterChange("platforms", [...currentPlatforms, platform]);
    }
  };

  const hasActiveFilters = Object.values(filters).some((val) =>
    Array.isArray(val) ? val.length < 3 : Boolean(val)
  );

  return (
    <div>
      <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="flex items-center gap-2">
          Filter
          {hasActiveFilters && (
            <Badge
              variant="secondary"
              className="h-5 w-5 p-0 flex items-center justify-center"
            >
              ✓
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[300px] sm:w-[400px] p-4">
        <SheetHeader>
          <SheetTitle className="text-left">Filters</SheetTitle>
        </SheetHeader>
        <div className="mt-6 space-y-6">
          {/* Cuisine Type */}
          <div className="space-y-2">
            <Label htmlFor="cuisine-type">Cuisine Type</Label>
            <Input
              id="cuisine-type"
              placeholder="Any cuisine"
              value={filters.cuisineType}
              onChange={(e) =>
                handleFilterChange("cuisineType", e.target.value)
              }
            />
          </div>

          {/* Min Rating */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="min-rating">Minimum Rating</Label>
              <span className="text-sm">{filters.minRating}+</span>
            </div>
            <Slider
              id="min-rating"
              defaultValue={[filters.minRating]}
              max={5}
              step={0.5}
              onValueChange={(vals) => handleFilterChange("minRating", vals[0])}
              className="pt-2"
            />
          </div>

          {/* Max Delivery Time */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="max-delivery">Max Delivery Time</Label>
              <span className="text-sm">{filters.maxDeliveryTime} min</span>
            </div>
            <Slider
              id="max-delivery"
              defaultValue={[filters.maxDeliveryTime]}
              min={15}
              max={90}
              step={5}
              onValueChange={(vals) =>
                handleFilterChange("maxDeliveryTime", vals[0])
              }
              className="pt-2"
            />
          </div>

          {/* Platforms */}
          <div className="space-y-2">
            <Label>Platforms</Label>
            <div className="flex flex-wrap gap-2">
              {["foodpanda", "foodi"].map((platform) => (
                <Badge
                  key={platform}
                  variant={
                    filters.platforms.includes(platform) ? "default" : "outline"
                  }
                  className="cursor-pointer"
                  onClick={() => handlePlatformToggle(platform)}
                >
                  {platform === "foodpanda"
                    ? "FoodPanda"
                    : platform === "ubereats"
                    ? "Uber Eats"
                    : "Pathao"}
                </Badge>
              ))}
            </div>
          </div>

          {/* Apply Filters Button */}
          <div className="pt-4">
            <SheetClose asChild>
              <Button className="w-full" variant="default">
                Apply Filters
              </Button>
            </SheetClose>
          </div>
        </div>
      </SheetContent>
    </Sheet>
    </div>
    
  );
}