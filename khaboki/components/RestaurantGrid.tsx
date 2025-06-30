/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useState } from "react";
import { RestaurantCard } from "./RestaurantCard";
import { RestaurantComparison } from "./RestaurantComparison";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Restaurant, ScrapeResults, SearchFiltersType } from "@/types";
import { X, BarChart3 } from "lucide-react";
import { calculateBayesianRating } from "@/lib/calculateBayesianRating";

interface RestaurantGridProps {
  restaurants: ScrapeResults;
  filters: SearchFiltersType;
  cuisineSearch?: string;
}

export function RestaurantGrid({
  restaurants,
  filters,
  cuisineSearch = "",
}: RestaurantGridProps) {
  const [compareList, setCompareList] = useState<Restaurant[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [useBayesianRating, setUseBayesianRating] = useState(true);

  const allRestaurants = [
    ...(restaurants.foodpanda || []),
    ...(restaurants.foodi || []),
  ];

  // Filter restaurants based on search
  const filteredRestaurants = allRestaurants.filter((restaurant) => {
    if (!cuisineSearch) return true;

    const searchLower = cuisineSearch.toLowerCase();
    return (
      restaurant.name.toLowerCase().includes(searchLower) ||
      restaurant.cuisine_type.toLowerCase().includes(searchLower)
    );
  });

  const foodpandaFiltered = (restaurants.foodpanda || []).filter(
    (restaurant) => {
      if (!cuisineSearch) return true;
      const searchLower = cuisineSearch.toLowerCase();
      return (
        restaurant.name.toLowerCase().includes(searchLower) ||
        restaurant.cuisine_type.toLowerCase().includes(searchLower)
      );
    }
  );

  const foodiFiltered = (restaurants.foodi || []).filter((restaurant) => {
    if (!cuisineSearch) return true;
    const searchLower = cuisineSearch.toLowerCase();
    return (
      restaurant.name.toLowerCase().includes(searchLower) ||
      restaurant.cuisine_type.toLowerCase().includes(searchLower)
    );
  });

  const foodpandaCount = foodpandaFiltered.length;
  const foodiCount = foodiFiltered.length;

  const handleCompare = (restaurant: Restaurant) => {
    if (
      compareList.length < 3 &&
      !compareList.find((r) => r.name === restaurant.name)
    ) {
      const newCompareList = [...compareList, restaurant];
      setCompareList(newCompareList);

      if (newCompareList.length >= 2) {
        setShowComparison(true);
      }
    }
  };

  const removeFromCompare = (restaurantName: string) => {
    setCompareList(compareList.filter((r) => r.name !== restaurantName));
  };

  const clearCompareList = () => {
    setCompareList([]);
    setShowComparison(false);
  };

  const sortRestaurants = (restaurants: Restaurant[]) => {
    return [...restaurants].sort((a, b) => {
      switch (filters.sortBy) {
        case "rating":
          const ratingA = calculateBayesianRating(
            a.rating,
            "all"
          ).adjustedRating;
          const ratingB = calculateBayesianRating(
            b.rating,
            "all"
          ).adjustedRating;
          return ratingB - ratingA;
        case "delivery_time":
          const timeA = parseInt(a.delivery_time.match(/(\d+)/)?.[1] || "999");
          const timeB = parseInt(b.delivery_time.match(/(\d+)/)?.[1] || "999");
          return timeA - timeB;
        default:
          return 0;
      }
    });
  };

  const isRestaurantInCompareList = (restaurant: Restaurant) => {
    return compareList.some((r) => r.name === restaurant.name);
  };

  return (
    <div className="space-y-6">
      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-surface-900">
            Found {filteredRestaurants.length} restaurants
            {cuisineSearch && (
              <span className="text-lg font-normal text-surface-600 ml-2">
                for &quot;{cuisineSearch}&quot;
              </span>
            )}
          </h2>
          <div className="flex gap-2">
            {foodpandaCount > 0 && (
              <Badge
                variant="secondary"
                className="bg-platform-foodpanda/10 text-platform-foodpanda border-platform-foodpanda/20"
              >
                FoodPanda: {foodpandaCount}
              </Badge>
            )}
            {foodiCount > 0 && (
              <Badge
                variant="secondary"
                className="bg-platform-foodi/10 text-platform-foodi border-platform-foodi/20"
              >
                Foodi: {foodiCount}
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Compare Section */}
      {compareList.length > 0 && (
        <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-blue-900">
              Comparing ({compareList.length}/3)
            </h3>
            <div className="flex gap-2">
              <Dialog open={showComparison} onOpenChange={setShowComparison}>
                <DialogTrigger asChild>
                  <Button
                    size="sm"
                    disabled={compareList.length < 2}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <BarChart3 size={16} className="mr-2" />
                    Compare Now
                  </Button>
                </DialogTrigger>
                <DialogContent className="md:min-w-5xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Restaurant Comparison</DialogTitle>
                  </DialogHeader>
                  <RestaurantComparison
                    restaurants={compareList}
                    onRemove={removeFromCompare}
                  />
                </DialogContent>
              </Dialog>

              <Button
                variant="outline"
                size="sm"
                onClick={clearCompareList}
                className="text-red-600 hover:text-red-700 border-red-200 hover:bg-red-50"
              >
                <X size={16} className="mr-1" />
                Clear All
              </Button>
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            {compareList.map((restaurant, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="flex items-center gap-2 px-3 py-1 bg-white border border-blue-300"
              >
                <span className="text-sm font-medium">{restaurant.name}</span>
                <button
                  onClick={() => removeFromCompare(restaurant.name)}
                  className="text-red-500 hover:text-red-700 ml-1"
                  title="Remove from comparison"
                >
                  <X size={14} />
                </button>
              </Badge>
            ))}
          </div>

          {compareList.length >= 2 && (
            <p className="text-xs text-blue-600 mt-2">
              ✨ You can compare {compareList.length} restaurants now!
            </p>
          )}
        </div>
      )}

      {/* Platform Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 bg-surface-100">
          <TabsTrigger value="all" className="data-[state=active]:bg-white">
            All Platforms ({filteredRestaurants.length})
          </TabsTrigger>
          <TabsTrigger
            value="foodpanda"
            className="data-[state=active]:bg-white"
          >
            FoodPanda ({foodpandaCount})
          </TabsTrigger>
          <TabsTrigger value="foodi" className="data-[state=active]:bg-white">
            Foodi ({foodiCount})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortRestaurants(filteredRestaurants).map((restaurant, index) => (
              <RestaurantCard
                key={`${restaurant.platform}-${index}`}
                restaurant={restaurant}
                onCompare={handleCompare}
                showCompareButton={compareList.length < 3}
                isInCompareList={isRestaurantInCompareList(restaurant)}
                useBayesianRating={useBayesianRating}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="foodpanda" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortRestaurants(foodpandaFiltered).map((restaurant, index) => (
              <RestaurantCard
                key={`foodpanda-${index}`}
                restaurant={restaurant}
                onCompare={handleCompare}
                showCompareButton={compareList.length < 3}
                isInCompareList={isRestaurantInCompareList(restaurant)}
                useBayesianRating={useBayesianRating}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="foodi" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortRestaurants(foodiFiltered).map((restaurant, index) => (
              <RestaurantCard
                key={`foodi-${index}`}
                restaurant={restaurant}
                onCompare={handleCompare}
                showCompareButton={compareList.length < 3}
                isInCompareList={isRestaurantInCompareList(restaurant)}
                useBayesianRating={useBayesianRating}
              />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
