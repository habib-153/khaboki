"use client";

import Image from "next/image";
import {
  Star,
  Clock,
  DollarSign,
  ExternalLink,
  Plus,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Restaurant } from "@/types";
import { calculateBayesianRating } from "@/lib/calculateBayesianRating";

interface RestaurantCardProps {
  restaurant: Restaurant;
  onCompare?: (restaurant: Restaurant) => void;
  showCompareButton?: boolean;
  isInCompareList?: boolean;
  useBayesianRating?: boolean; 
}

export function RestaurantCard({
  restaurant,
  onCompare,
  showCompareButton = false,
  isInCompareList = false,
  useBayesianRating = false,
}: RestaurantCardProps) {
  const formatRating = (rating: string) => {
    if (rating === "No rating") return "No rating";
    const match = rating.match(/(\d+\.?\d*)/);
    return match ? `${match[1]} ★` : rating;
  };

  const formatDeliveryTime = (time: string) => {
    if (time === "Unknown" || !time) return "Time varies";
    return time.includes("min") ? time : `${time} min`;
  };

  const formatDeliveryFee = (fee: string) => {
    if (fee === "Unknown" || !fee) return "Fee varies";
    if (fee === "৳") return "Check app";
    return fee;
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "foodpanda":
        return "bg-pink-500 hover:bg-pink-600";
      case "foodi":
        return "bg-red-500 hover:bg-red-600";
      default:
        return "bg-gray-500 hover:bg-gray-600";
    }
  };

  const bayesianData = calculateBayesianRating(
        restaurant.rating,
        restaurant.platform.toLowerCase()
      )
    
  const displayRating =
    useBayesianRating && bayesianData
      ? `${bayesianData.adjustedRating} ★ (Adj.)`
      : formatRating(restaurant.rating);

      const getRatingColor = (rating: string) => {
        const ratingToUse =
          useBayesianRating && bayesianData
            ? bayesianData.adjustedRating.toString()
            : rating;

        const numRating = parseFloat(
          ratingToUse.match(/(\d+\.?\d*)/)?.[1] || "0"
        );
        if (numRating >= 4.5) return "text-green-600 bg-green-50";
        if (numRating >= 4.0) return "text-blue-600 bg-blue-50";
        if (numRating >= 3.5) return "text-yellow-600 bg-yellow-50";
        return "text-red-600 bg-red-50";
      };

  return (
    <Card
      className={`overflow-hidden hover:shadow-lg transition-all duration-300 group ${
        isInCompareList ? "ring-2 ring-blue-500 shadow-lg" : ""
      }`}
    >
      {/* Image Section */}
      <div className="relative h-48 overflow-hidden">
        <Image
          src={
            restaurant.image_url ||
            "https://via.placeholder.com/400x200?text=No+Image"
          }
          alt={restaurant.name}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-300"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />

        <div className="absolute top-3 right-3 flex gap-2">
          <Badge
            className={`${getPlatformColor(restaurant.platform)} text-white`}
          >
            {restaurant.platform}
          </Badge>
          {isInCompareList && (
            <Badge className="bg-blue-600 text-white">
              <Check size={12} className="mr-1" />
              Comparing
            </Badge>
          )}
        </div>

        {/* Offers Section - NEW */}
        {restaurant.offers && restaurant.offers.length > 0 && (
          <div className="absolute top-3 left-3 flex flex-col gap-1">
            {restaurant.offers.slice(0, 2).map((offer, index) => (
              <Badge
                key={index}
                className="bg-red-500 text-white text-xs font-bold animate-pulse"
              >
                {offer}
              </Badge>
            ))}
            {restaurant.offers.length > 2 && (
              <Badge className="bg-red-600 text-white text-xs">
                +{restaurant.offers.length - 2} more
              </Badge>
            )}
          </div>
        )}

        {/* Quick Info Overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
          <div className="flex items-center justify-between text-white text-sm">
            <div className="flex items-center gap-1">
              <Star size={14} className="text-yellow-400" />
              <span>{formatRating(restaurant.rating)}</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={14} />
              <span>{formatDeliveryTime(restaurant.delivery_time)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <CardHeader className="pb-2">
        <h3 className="font-semibold text-lg leading-tight line-clamp-2 min-h-[3.5rem]">
          {restaurant.name}
        </h3>

        {restaurant.offers && restaurant.offers.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {restaurant.offers.map((offer, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="text-xs bg-red-50 text-red-700 border border-red-200"
              >
                🎉 {offer}
              </Badge>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600 capitalize">
            {restaurant.cuisine_type || "Various cuisines"}
          </p>
          <div className="flex items-center gap-1 text-sm text-green-600 font-medium">
            <DollarSign size={14} />
            <span>{formatDeliveryFee(restaurant.delivery_fee)}</span>
          </div>
        </div>

        {/* Rating Badge */}
        <div className="flex items-center gap-2">
          <Badge className={`${getRatingColor(restaurant.rating)} border-none`}>
            {displayRating}
          </Badge>

          {/* Show confidence indicator for Bayesian ratings */}
          {useBayesianRating && bayesianData && (
            <Badge
              variant="outline"
              className={`text-xs ${
                bayesianData.confidence === "high"
                  ? "border-green-500 text-green-700"
                  : bayesianData.confidence === "medium"
                  ? "border-yellow-500 text-yellow-700"
                  : "border-red-500 text-red-700"
              }`}
            >
              {bayesianData.confidence}
            </Badge>
          )}

          <span className="text-xs text-gray-500">
            {formatDeliveryTime(restaurant.delivery_time)}
          </span>
        </div>
      </CardHeader>

      {/* Footer Actions */}
      <CardFooter className="pt-0 flex gap-2">
        <a
          href={restaurant.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1"
        >
          <Button
            variant="outline"
            className="w-full hover:bg-primary hover:text-primary-foreground transition-colors"
          >
            <ExternalLink size={16} className="mr-2" />
            Order Now
          </Button>
        </a>

        {showCompareButton && onCompare && (
          <Button
            variant={isInCompareList ? "default" : "secondary"}
            size="sm"
            onClick={() => onCompare(restaurant)}
            disabled={isInCompareList}
            className={`px-3 hover:shadow hover:cursor-pointer ${
              isInCompareList ? "bg-blue-600 hover:bg-blue-700" : ""
            }`}
            title={
              isInCompareList ? "Already in comparison" : "Add to comparison"
            }
          >
            {isInCompareList ? <Check size={16} /> : <Plus size={16} />}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}