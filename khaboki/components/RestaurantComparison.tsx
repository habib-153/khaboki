/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import Image from "next/image";
import {
  Star,
  Clock,
  DollarSign,
  ExternalLink,
  X,
  Award,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Restaurant } from "@/types";
import { calculateBayesianRating } from "@/lib/calculateBayesianRating";

interface RestaurantComparisonProps {
  restaurants: Restaurant[];
  onRemove: (restaurantName: string) => void;
}

export function RestaurantComparison({
  restaurants,
  onRemove,
}: RestaurantComparisonProps) {
  const formatRating = (
    rating: string,
    platform = "all"
  ) => {
    if (rating === "No rating") return { value: 0, display: "No rating" };

    
      const bayesianData = calculateBayesianRating(
        rating,
        platform.toLowerCase()
      );
      return {
        value: bayesianData.adjustedRating,
        display: `${bayesianData.adjustedRating} ★ (Adj.)`,
        confidence: bayesianData.confidence,
        originalValue: parseFloat(rating.match(/(\d+\.?\d*)/)?.[1] || "0"),
        originalDisplay: rating.match(/(\d+\.?\d*)/)
          ? `${rating.match(/(\d+\.?\d*)/)?.[1]} ★`
          : rating,
      };
  };

  const formatDeliveryTime = (time: string) => {
    if (time === "Unknown" || !time)
      return { value: 999, display: "Time varies" };
    const match = time.match(/(\d+)/);
    const numValue = match ? parseInt(match[1]) : 999;
    return {
      value: numValue,
      display: time.includes("min") ? time : `${time} min`,
    };
  };

  const formatDeliveryFee = (fee: string) => {
    if (fee === "Unknown" || !fee) return { value: 999, display: "Fee varies" };
    if (fee === "৳") return { value: 999, display: "Check app" };
    const match = fee.match(/(\d+)/);
    const numValue = match ? parseInt(match[1]) : 999;
    return { value: numValue, display: fee };
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "foodpanda":
        return "bg-pink-500";
      case "foodi":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  // Find best values for highlighting
  const ratings = restaurants.map(
    (r) => formatRating(r.rating, r.platform).value
  );
  const deliveryTimes = restaurants.map(
    (r) => formatDeliveryTime(r.delivery_time).value
  );
  const deliveryFees = restaurants.map(
    (r) => formatDeliveryFee(r.delivery_fee).value
  );

  const bestRating = Math.max(...ratings.filter((r) => r > 0));
  const bestDeliveryTime = Math.min(...deliveryTimes.filter((t) => t < 999));
  const bestDeliveryFee = Math.min(...deliveryFees.filter((f) => f < 999));

  const ComparisonMetric = ({
    icon: Icon,
    label,
    values,
    bestValue,
    isBetterWhenHigher = false,
    showConfidence = false,
  }: {
    icon: any;
    label: string;
    values: {
      value: number;
      display: string;
      confidence?: string;
      originalDisplay?: string;
    }[];
    bestValue: number;
    isBetterWhenHigher?: boolean;
    showConfidence?: boolean;
  }) => (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-600">
        <Icon size={16} />
        {label}
      </div>
      <div
        className="grid gap-2"
        style={{ gridTemplateColumns: `repeat(${restaurants.length}, 1fr)` }}
      >
        {values.map((value, index) => {
          const isBest = isBetterWhenHigher
            ? value.value === bestValue && value.value > 0
            : value.value === bestValue && value.value < 999;

          return (
            <div
              key={index}
              className={`p-2 rounded text-center text-sm font-medium ${
                isBest
                  ? "bg-green-100 text-green-800 border border-green-300"
                  : "bg-gray-50 text-gray-700"
              }`}
            >
              {isBest && <Award size={12} className="inline mr-1" />}
              <div>{value.display}</div>

              {/* Show original rating if using Bayesian */}
              {/* {showConfidence && value.originalDisplay && (
                <div className="text-xs text-gray-500 mt-1">
                  Original: {value.originalDisplay}
                </div>
              )} */}

              {/* Show confidence indicator */}
              {showConfidence && value.confidence && (
                <Badge
                  variant="outline"
                  className={`text-xs mt-1 ${
                    value.confidence === "high"
                      ? "border-green-500 text-green-700"
                      : value.confidence === "medium"
                      ? "border-yellow-500 text-yellow-700"
                      : "border-red-500 text-red-700"
                  }`}
                >
                  {value.confidence}
                </Badge>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Restaurant Cards Grid */}
      <div
        className="grid gap-4"
        style={{ gridTemplateColumns: `repeat(${restaurants.length}, 1fr)` }}
      >
        {restaurants.map((restaurant, index) => (
          <Card key={index} className="relative">
            <button
              onClick={() => onRemove(restaurant.name)}
              className="absolute top-2 right-2 z-10 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              title="Remove from comparison"
            >
              <X size={12} />
            </button>

            <div className="relative h-32 overflow-hidden rounded-t-lg">
              <Image
                src={
                  restaurant.image_url ||
                  "https://via.placeholder.com/300x150?text=No+Image"
                }
                alt={restaurant.name}
                fill
                className="object-cover"
                sizes="300px"
              />
              <Badge
                className={`absolute top-2 left-2 ${getPlatformColor(
                  restaurant.platform
                )} text-white`}
              >
                {restaurant.platform}
              </Badge>
            </div>

            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold line-clamp-2 min-h-[2.5rem]">
                {restaurant.name}
              </CardTitle>
              <p className="text-xs text-gray-600 capitalize">
                {restaurant.cuisine_type || "Various cuisines"}
              </p>
            </CardHeader>

            <CardContent className="pt-0">
              <a
                href={restaurant.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full"
              >
                <Button size="sm" className="w-full">
                  <ExternalLink size={14} className="mr-2" />
                  Order Now
                </Button>
              </a>
            </CardContent>
          </Card>
        ))}
      </div>

      <Separator />

      {/* Comparison Metrics */}
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">Comparison Details</h3>

        <ComparisonMetric
          icon={Star}
          label={"Rating (Bayesian Adjusted)"}
          values={restaurants.map((r) => formatRating(r.rating, r.platform))}
          bestValue={bestRating}
          isBetterWhenHigher={true}
          showConfidence={true}
        />

        <ComparisonMetric
          icon={Clock}
          label="Delivery Time"
          values={restaurants.map((r) => formatDeliveryTime(r.delivery_time))}
          bestValue={bestDeliveryTime}
        />

        <ComparisonMetric
          icon={DollarSign}
          label="Delivery Fee"
          values={restaurants.map((r) => formatDeliveryFee(r.delivery_fee))}
          bestValue={bestDeliveryFee}
        />

        {/* Cuisine Types */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-600">
            <MapPin size={16} />
            Cuisine Type
          </div>
          <div
            className="grid gap-2"
            style={{
              gridTemplateColumns: `repeat(${restaurants.length}, 1fr)`,
            }}
          >
            {restaurants.map((restaurant, index) => (
              <div
                key={index}
                className="p-2 bg-gray-50 rounded text-center text-sm capitalize"
              >
                {restaurant.cuisine_type || "Various"}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">Quick Summary</h4>
        <div className="grid gap-2 text-sm">
          {bestRating > 0 && (
            <div className="flex items-center gap-2">
              <Award size={14} className="text-green-600" />
              <span>
                Best rated:{" "}
                {
                  restaurants.find(
                    (r) =>
                      formatRating(r.rating,  r.platform)
                        .value === bestRating
                  )?.name
                }
                ({bestRating} ★)
                
                  <span className="text-xs text-gray-500 ml-1">
                    (Bayesian adjusted)
                  </span>
              </span>
            </div>
          )}
          {bestDeliveryTime < 999 && (
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-blue-600" />
              <span>
                Fastest delivery:{" "}
                {
                  restaurants.find(
                    (r) =>
                      formatDeliveryTime(r.delivery_time).value ===
                      bestDeliveryTime
                  )?.name
                }
                ({bestDeliveryTime} min)
              </span>
            </div>
          )}
          {bestDeliveryFee < 999 && (
            <div className="flex items-center gap-2">
              <DollarSign size={14} className="text-green-600" />
              <span>
                Cheapest delivery:{" "}
                {
                  restaurants.find(
                    (r) =>
                      formatDeliveryFee(r.delivery_fee).value ===
                      bestDeliveryFee
                  )?.name
                }
                (৳{bestDeliveryFee})
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}