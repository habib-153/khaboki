"use server";

import { Restaurant } from "@/types";
import { GoogleGenerativeAI } from "@google/generative-ai";

interface SurpriseRestaurantRequest {
  restaurants: Restaurant[];
  userPreferences?: {
    cuisineType?: string;
    maxDeliveryTime?: number;
    maxDeliveryFee?: number;
    minRating?: number;
  };
}

const generateSurpriseRestaurant = async (
  data: SurpriseRestaurantRequest,
  prompt: string
): Promise<Restaurant | null> => {
  try {
    const genAI = new GoogleGenerativeAI(
      process.env.NEXT_PUBLIC_GEMINI_API_KEY as string
    );
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    // Create a better structured prompt
    const fullPrompt = `
  ${prompt}
  
  Here's the restaurant data:
  ${JSON.stringify(data.restaurants, null, 2)}
  
  User preferences: ${JSON.stringify(data.userPreferences || {}, null, 2)}
  
  Please respond with a JSON object containing the selected restaurant data exactly as it appears in the input data. Return only the JSON object, no additional text.
  `;

    const result = await model.generateContent(fullPrompt);
    const response = await result.response;
    const text = response.text();

    // Parse the JSON response
    try {
      const cleanedText = text.replace(/```json|```/g, "").trim();
      const selectedRestaurant = JSON.parse(cleanedText);
      return selectedRestaurant;
    } catch (parseError) {
      console.error("Failed to parse AI response:", parseError);
      // Fallback: return a random restaurant
      return data.restaurants[
        Math.floor(Math.random() * data.restaurants.length)
      ];
    }
  } catch (error) {
    console.error("Error generating surprise restaurant:", error);
    return null;
  }
};

export default generateSurpriseRestaurant;