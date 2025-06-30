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
}

export function RestaurantGrid({ restaurants, filters }: RestaurantGridProps) {
  const [compareList, setCompareList] = useState<Restaurant[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [sortBy, setSortBy] = useState<"rating" | "name" | "delivery_time">(
    "rating"
  );
  const [useBayesianRating, setUseBayesianRating] = useState(true);

  const allRestaurants = [
    ...(restaurants.foodpanda || []),
    ...(restaurants.foodi || []),
  ];

  const foodpandaCount = restaurants.foodpanda?.length || 0;
  const foodiCount = restaurants.foodi?.length || 0;

  const handleCompare = (restaurant: Restaurant) => {
    if (
      compareList.length < 3 &&
      !compareList.find((r) => r.name === restaurant.name)
    ) {
      const newCompareList = [...compareList, restaurant];
      setCompareList(newCompareList);

      // Auto-open comparison modal when 2+ restaurants are selected
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
      switch (sortBy) {
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
        case "name":
          return a.name.localeCompare(b.name);
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
      {/* <div className="flex items-center gap-4">
        <div className="flex items-center space-x-2">
          <Switch
            id="bayesian-rating"
            checked={useBayesianRating}
            onCheckedChange={setUseBayesianRating}
          />
          <Label htmlFor="bayesian-rating">Use Bayesian Rating</Label>
        </div>
      </div> */}
      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">
            Found {allRestaurants.length} restaurants
          </h2>
          <div className="flex gap-2">
            {foodpandaCount > 0 && (
              <Badge variant="secondary" className="bg-pink-100 text-pink-800">
                FoodPanda: {foodpandaCount}
              </Badge>
            )}
            {foodiCount > 0 && (
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                Foodi: {foodiCount}
              </Badge>
            )}
          </div>
        </div>

        {/* Sort Options */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Sort by:</span>
          <Button
            variant={sortBy === "rating" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("rating")}
          >
            Rating
          </Button>
          <Button
            variant={sortBy === "delivery_time" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("delivery_time")}
          >
            Delivery Time
          </Button>
          <Button
            variant={sortBy === "name" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("name")}
          >
            Name
          </Button>
        </div>
      </div>

      {/* Compare Section */}
      {compareList.length > 0 && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
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
                className="text-red-600 hover:text-red-700"
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all">
            All Platforms ({allRestaurants.length})
          </TabsTrigger>
          <TabsTrigger value="foodpanda">
            FoodPanda ({foodpandaCount})
          </TabsTrigger>
          <TabsTrigger value="foodi">Foodi ({foodiCount})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortRestaurants(allRestaurants).map((restaurant, index) => (
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
            {sortRestaurants(restaurants.foodpanda || []).map(
              (restaurant, index) => (
                <RestaurantCard
                  key={`foodpanda-${index}`}
                  restaurant={restaurant}
                  onCompare={handleCompare}
                  showCompareButton={compareList.length < 3}
                  isInCompareList={isRestaurantInCompareList(restaurant)}
                  useBayesianRating={useBayesianRating}
                />
              )
            )}
          </div>
        </TabsContent>

        <TabsContent value="foodi" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortRestaurants(restaurants.foodi || []).map(
              (restaurant, index) => (
                <RestaurantCard
                  key={`foodi-${index}`}
                  restaurant={restaurant}
                  onCompare={handleCompare}
                  showCompareButton={compareList.length < 3}
                  isInCompareList={isRestaurantInCompareList(restaurant)}
                  useBayesianRating={useBayesianRating}
                />
              )
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
