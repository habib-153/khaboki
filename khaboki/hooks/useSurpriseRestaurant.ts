/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { Restaurant, ScrapeResults } from "@/types";
import generateSurpriseRestaurant from "@/lib/getSurpriseRestaurent";

export const useSurpriseRestaurant = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [surpriseRestaurant, setSurpriseRestaurant] =
    useState<Restaurant | null>(null);
  const [previousSuggestions, setPreviousSuggestions] = useState<Restaurant[]>(
    []
  );

  const getSurpriseRestaurant = async (
    restaurants: ScrapeResults,
    userPreferences?: any,
    excludePrevious: boolean = false
  ) => {
    setIsLoading(true);
    try {
      const allRestaurants = [
        ...(restaurants.foodpanda || []),
        ...(restaurants.foodi || []),
      ];

      if (allRestaurants.length === 0) {
        throw new Error("No restaurants available");
      }

      // Filter out previously suggested restaurants if requested
      let availableRestaurants = allRestaurants;
      if (excludePrevious && previousSuggestions.length > 0) {
        availableRestaurants = allRestaurants.filter(
          (restaurant) =>
            !previousSuggestions.some(
              (prev) =>
                prev.name === restaurant.name &&
                prev.platform === restaurant.platform
            )
        );

        // If we've suggested all restaurants, reset and use all restaurants
        if (availableRestaurants.length === 0) {
          availableRestaurants = allRestaurants;
          setPreviousSuggestions([]); // Reset the history
          console.log("Reset suggestion history - all restaurants were tried");
        }
      }

      const prompt = `
You are an intelligent restaurant discovery agent. I have provided you with detailed, up-to-date data scraped from multiple food delivery platforms, including each restaurant's:
Name, cuisine types, price range, Average rating and number of reviews per platform, Delivery time and distance from the user's location
,Availability status, Any special offers or highlights (e.g., "New on platform", "Top rated", etc.).

Your task is to pick a restaurant that the user is most likely to enjoy but may not have tried yet – this is for a "Surprise Me" button. You must balance quality, novelty, and availability.

${
  excludePrevious
    ? `
IMPORTANT: The user has requested a NEW suggestion. Do NOT suggest any restaurant that appears to be similar to their previous picks. Choose something completely different in terms of cuisine, style, or restaurant type.
`
    : ""
}

Use the following logic:
Prioritize restaurants with strong reviews and enough number of reviews to be reliable. Use Bayesian or weighted average methods if needed.
Prefer restaurants that are either new and promising or highly rated but not in the user's usual picks (assume we want to avoid repetition).
Consider diversity in cuisine and price points so the surprise feels fresh and worth exploring.
The restaurant must be delivering now and within a reasonable distance or delivery time.
${
  excludePrevious
    ? "Focus on variety and completely different options from what might have been suggested before."
    : ""
}
`;

      const result = await generateSurpriseRestaurant(
        { restaurants: availableRestaurants, userPreferences },
        prompt
      );

      if (result) {
        setSurpriseRestaurant(result);
        // Add to previous suggestions if this was a "try another" request
        if (excludePrevious) {
          setPreviousSuggestions((prev) => [...prev, result]);
        } else {
          // If it's a fresh start, reset previous suggestions
          setPreviousSuggestions([result]);
        }
      }

      return result;
    } catch (error) {
      console.error("Error getting surprise restaurant:", error);

      // Fallback to random selection, but still respect the exclusion logic
      const allRestaurants = [
        ...(restaurants.foodpanda || []),
        ...(restaurants.foodi || []),
      ];

      let availableRestaurants = allRestaurants;
      if (excludePrevious && previousSuggestions.length > 0) {
        availableRestaurants = allRestaurants.filter(
          (restaurant) =>
            !previousSuggestions.some(
              (prev) =>
                prev.name === restaurant.name &&
                prev.platform === restaurant.platform
            )
        );

        if (availableRestaurants.length === 0) {
          availableRestaurants = allRestaurants;
          setPreviousSuggestions([]);
        }
      }

      const randomRestaurant =
        availableRestaurants[
          Math.floor(Math.random() * availableRestaurants.length)
        ];
      setSurpriseRestaurant(randomRestaurant);

      if (randomRestaurant) {
        if (excludePrevious) {
          setPreviousSuggestions((prev) => [...prev, randomRestaurant]);
        } else {
          setPreviousSuggestions([randomRestaurant]);
        }
      }

      return randomRestaurant;
    } finally {
      setIsLoading(false);
    }
  };

  const resetSuggestions = () => {
    setPreviousSuggestions([]);
    setSurpriseRestaurant(null);
  };

  return {
    getSurpriseRestaurant,
    surpriseRestaurant,
    isLoading,
    setSurpriseRestaurant,
    previousSuggestions,
    resetSuggestions,
  };
};