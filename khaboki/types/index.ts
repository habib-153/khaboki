export interface Restaurant {
  name: string;
  cuisine_type: string;
  rating: string;
  delivery_time: string;
  delivery_fee: string;
  platform: string;
  image_url: string;
  url: string;
  menu_items: unknown[];
  offers?: string[];
}

export interface ScrapeResults {
  foodpanda?: Restaurant[];
  foodi?: Restaurant[];
}

export interface LocationCoordinates {
  lat: number;
  lng: number;
}

export interface SearchFiltersType
 {
  cuisineType: string;
  minRating: number;
  maxDeliveryTime: number;
  platforms: string[];
  maxDeliveryFee?: number;
  sortBy?: "rating" | "delivery_time" | "delivery_fee" | "name";
}

export interface CacheInfo {
  hasCache: boolean;
  lastLocation?: LocationCoordinates;
  timestamp?: number;
}

export interface ApiResponse {
  success: boolean;
  results?: ScrapeResults;
  error?: string;
}

export interface DatasetStats {
  total_restaurants: number;
  platform_breakdown: Record<string, number>;
  last_updated: string;
}

export interface SurpriseModalProps {
  isOpen: boolean;
  onClose: () => void;
  restaurant: Restaurant | null;
  onRefresh: () => void;
  isLoading: boolean;
  previousCount?: number;
}