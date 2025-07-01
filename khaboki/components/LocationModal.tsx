/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { MapPin, Search, Loader2, Navigation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLocationSelect: (
    location: { lat: number; lng: number },
    address: string
  ) => void;
  initialLocation?: { lat: number; lng: number } | null;
  initialAddress?: string;
  isLoading?: boolean;
}

export function LocationModal({
  isOpen,
  onClose,
  onLocationSelect,
  initialLocation,
  initialAddress = "",
  isLoading = false,
}: LocationModalProps) {
  const [searchValue, setSearchValue] = useState(initialAddress);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(initialLocation || null);
  const [currentAddress, setCurrentAddress] = useState(initialAddress);
  const [gettingLocation, setGettingLocation] = useState(false);

  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const geocoderRef = useRef<google.maps.Geocoder | null>(null);
  const mapInitializedRef = useRef<boolean>(false);

  // Reverse geocode to get address from coordinates
  const reverseGeocode = useCallback((lat: number, lng: number) => {
    if (!geocoderRef.current) return;

    const request: google.maps.GeocoderRequest = {
      location: { lat, lng },
    };

    geocoderRef.current.geocode(request, (results, status) => {
      if (status === "OK" && results && results[0]) {
        const address = results[0].formatted_address;
        setSearchValue(address);
        setCurrentAddress(address);
      }
    });
  }, []);

  // Get user's current location
  const getCurrentLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by this browser.");
      return;
    }

    setGettingLocation(true);

    try {
      const position = await new Promise<GeolocationPosition>(
        (resolve, reject) => {
          const timeoutId = setTimeout(() => {
            reject(new Error("Location request timed out. Please try again."));
          }, 15000);

          navigator.geolocation.getCurrentPosition(
            (position) => {
              clearTimeout(timeoutId);
              resolve(position);
            },
            (error) => {
              clearTimeout(timeoutId);
              switch (error.code) {
                case error.PERMISSION_DENIED:
                  reject(
                    new Error(
                      "Location access denied. Please enable location permissions in your browser."
                    )
                  );
                  break;
                case error.POSITION_UNAVAILABLE:
                  reject(
                    new Error(
                      "Location information is unavailable. Please search for your address manually."
                    )
                  );
                  break;
                case error.TIMEOUT:
                  reject(
                    new Error("Location request timed out. Please try again.")
                  );
                  break;
                default:
                  reject(new Error(`Location error: ${error.message}`));
              }
            },
            {
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 0,
            }
          );
        }
      );

      if (!position?.coords) {
        throw new Error("Could not get coordinates from your device");
      }

      const { latitude, longitude, accuracy } = position.coords;
      console.log(
        `GPS Location: ${latitude}, ${longitude} (accuracy: ${accuracy}m)`
      );

      if (accuracy > 1000) {
        console.warn(`Low GPS accuracy: ${accuracy} meters`);
      }

      const location = { lat: latitude, lng: longitude };
      setSelectedLocation(location);

      if (mapRef.current && markerRef.current) {
        mapRef.current.setCenter(location);
        mapRef.current.setZoom(16);
        markerRef.current.setPosition(location);
      }

      // Get detailed address using Google Geocoding API
      try {
        const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${latitude},${longitude}&key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&language=en`;

        const response = await fetch(geocodeUrl);

        if (!response.ok) {
          throw new Error(`Geocoding failed: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === "OK" && data.results?.[0]) {
          const result = data.results[0];

          let street = "",
            city = "",
            area = "",
            district = "",
            division = "";

          result.address_components.forEach((component: any) => {
            const types = component.types;

            if (types.includes("street_number") || types.includes("route")) {
              street = street
                ? `${street} ${component.long_name}`
                : component.long_name;
            }
            if (
              types.includes("sublocality_level_1") ||
              types.includes("neighborhood")
            ) {
              area = component.long_name;
            }
            if (
              types.includes("locality") ||
              types.includes("administrative_area_level_2")
            ) {
              city = component.long_name;
            }
            if (types.includes("administrative_area_level_1")) {
              division = component.long_name;
            }
            if (types.includes("sublocality_level_2")) {
              district = component.long_name;
            }
          });

          let formattedAddress = "";
          if (street) formattedAddress += street;
          if (area && area !== city) {
            formattedAddress += formattedAddress ? `, ${area}` : area;
          }
          if (city) {
            formattedAddress += formattedAddress ? `, ${city}` : city;
          }
          if (division && division !== city) {
            formattedAddress += formattedAddress ? `, ${division}` : division;
          }

          if (!formattedAddress || formattedAddress.length < 10) {
            formattedAddress = result.formatted_address;
          }

          setSearchValue(formattedAddress);
          setCurrentAddress(formattedAddress);

          console.log("Detailed address:", {
            street,
            area,
            city,
            district,
            division,
            formatted: formattedAddress,
          });
        } else {
          console.warn("Geocoding API returned no results, using coordinates");
          reverseGeocode(latitude, longitude);
        }
      } catch (geocodeError) {
        console.error("Google Geocoding failed, using fallback:", geocodeError);
        reverseGeocode(latitude, longitude);
      }
    } catch (error: any) {
      console.error("Location error:", error);

      if (error.message.includes("denied")) {
        alert(
          "Location access denied. Please enable location permissions in your browser settings and try again."
        );
      } else if (error.message.includes("unavailable")) {
        alert(
          "Location information is unavailable. Please search for your address manually."
        );
      } else if (error.message.includes("timeout")) {
        alert(
          "Location request timed out. Please check your connection and try again."
        );
      } else {
        alert(
          `Unable to get your location: ${error.message}. Please search for your address manually.`
        );
      }
    } finally {
      setGettingLocation(false);
    }
  }, [reverseGeocode]);

  // Initialize map
  const initializeMap = useCallback(() => {
    if (
      !mapContainerRef.current ||
      !window.google ||
      mapInitializedRef.current
    ) {
      return;
    }

    console.log("Initializing map...");

    const defaultCenter = initialLocation || { lat: 23.8007, lng: 90.4262 };

    const mapOptions: google.maps.MapOptions = {
      center: defaultCenter,
      zoom: 14,
      styles: [
        {
          featureType: "poi",
          elementType: "labels",
          stylers: [{ visibility: "off" }],
        },
      ],
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      zoomControl: true,
      zoomControlOptions: {
        position: window.google.maps.ControlPosition.RIGHT_CENTER,
      },
    };

    const map = new window.google.maps.Map(mapContainerRef.current, mapOptions);
    mapRef.current = map;
    mapInitializedRef.current = true;

    geocoderRef.current = new window.google.maps.Geocoder();

    const marker = new window.google.maps.Marker({
      position: defaultCenter,
      map: map,
      draggable: true,
      animation: window.google.maps.Animation.DROP,
      title: "Drag me to select location",
    });
    markerRef.current = marker;

    // Handle marker drag
    marker.addListener("dragend", () => {
      const position = marker.getPosition();
      if (position) {
        const location = {
          lat: position.lat(),
          lng: position.lng(),
        };
        setSelectedLocation(location);
        reverseGeocode(location.lat, location.lng);
      }
    });

    // Handle map click
    map.addListener("click", (e: google.maps.MapMouseEvent) => {
      const clickedLocation = {
        lat: e.latLng!.lat(),
        lng: e.latLng!.lng(),
      };

      setSelectedLocation(clickedLocation);
      marker.setPosition(clickedLocation);
      reverseGeocode(clickedLocation.lat, clickedLocation.lng);
    });

    // Setup autocomplete
    const inputElement = document.getElementById(
      "modal-location-search"
    ) as HTMLInputElement;

    if (inputElement) {
      const autocompleteOptions: google.maps.places.AutocompleteOptions = {
        fields: ["address_components", "geometry", "formatted_address"],
        types: ["address"],
        componentRestrictions: { country: "bd" },
      };

      const autocomplete = new window.google.maps.places.Autocomplete(
        inputElement,
        autocompleteOptions
      );

      autocomplete.bindTo("bounds", map);
      autocompleteRef.current = autocomplete;

      autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();

        if (!place.geometry || !place.geometry.location) {
          return;
        }

        const location = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
        };

        setSelectedLocation(location);
        setCurrentAddress(place.formatted_address || searchValue);
        setSearchValue(place.formatted_address || searchValue);
        map.setCenter(location);
        marker.setPosition(location);
        map.setZoom(17);

        // DO NOT auto-close modal here - let user confirm with button
        console.log(
          "Autocomplete selection made, waiting for user confirmation"
        );
      });
    }

    // Fix autocomplete dropdown z-index
    setTimeout(() => {
      const pacContainers = document.querySelectorAll(".pac-container");
      pacContainers.forEach((container) => {
        const htmlContainer = container as HTMLElement;
        htmlContainer.style.zIndex = "999999";
        htmlContainer.style.position = "absolute";
        htmlContainer.style.backgroundColor = "white";
        htmlContainer.style.border = "1px solid #e2e8f0";
        htmlContainer.style.borderRadius = "0.5rem";
        htmlContainer.style.boxShadow =
          "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)";
        htmlContainer.style.pointerEvents = "auto";
      });
    }, 500);
  }, [initialLocation, reverseGeocode, searchValue]);

  // Handle modal open/close
  useEffect(() => {
    if (isOpen && window.google) {
      // Clean up any existing map first
      if (mapRef.current) {
        mapRef.current = null;
        mapInitializedRef.current = false;
      }

      // Initialize map with delay to ensure modal is rendered
      setTimeout(() => {
        if (isOpen) {
          // Double check modal is still open
          initializeMap();
        }
      }, 300);
    }

    // Cleanup on close
    if (!isOpen) {
      const pacContainers = document.querySelectorAll(".pac-container");
      pacContainers.forEach((container) => {
        container.remove();
      });
      mapInitializedRef.current = false;
    }
  }, [isOpen, initializeMap]);

  // Enhanced z-index management for autocomplete
  useEffect(() => {
    if (isOpen) {
      const observer = new MutationObserver(() => {
        const pacContainers = document.querySelectorAll(".pac-container");
        pacContainers.forEach((container) => {
          const htmlContainer = container as HTMLElement;
          htmlContainer.style.zIndex = "999999";
          htmlContainer.style.position = "absolute";
          htmlContainer.style.backgroundColor = "white";
          htmlContainer.style.border = "1px solid #e2e8f0";
          htmlContainer.style.borderRadius = "0.5rem";
          htmlContainer.style.boxShadow =
            "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)";
          htmlContainer.style.pointerEvents = "auto";
          htmlContainer.style.minWidth = "250px";
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });

      return () => observer.disconnect();
    }
  }, [isOpen]);

  // Only close modal when user explicitly clicks "Find Restaurants"
  const handleFindRestaurants = () => {
    if (selectedLocation) {
      const addressToUse = currentAddress || searchValue;
      onLocationSelect(selectedLocation, addressToUse);
      onClose();
    }
  };

  // Reset states when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchValue(initialAddress);
      setCurrentAddress(initialAddress);
      setSelectedLocation(initialLocation || null);
    }
  }, [isOpen, initialAddress, initialLocation]);

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        // Only allow closing through explicit user action, not through autocomplete
        if (!open) {
          console.log("Dialog close requested");
          onClose();
        }
      }}
    >
      <DialogContent
        className="max-w-5xl w-full max-h-[90vh] overflow-y-auto"
        style={{ zIndex: 50 }}
        onPointerDownOutside={(e) => {
          // Prevent closing when clicking on autocomplete suggestions
          const target = e.target as Element;
          if (target.closest(".pac-container")) {
            e.preventDefault();
          }
        }}
        onEscapeKeyDown={(e) => {
          // Prevent escape key from closing during autocomplete interaction
          const pacContainers = document.querySelectorAll(".pac-container");
          if (pacContainers.length > 0) {
            e.preventDefault();
          }
        }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-brand-primary" />
            Select Your Location
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input with Get Current Location button */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                id="modal-location-search"
                placeholder="Enter your address or use current location..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="pl-10 h-12 border-surface-300 focus:border-brand-primary focus:ring-brand-primary/20"
                autoComplete="off"
              />
              <MapPin
                size={18}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-surface-400"
              />
            </div>
            <Button
              onClick={getCurrentLocation}
              disabled={gettingLocation}
              variant="outline"
              className="h-12 px-4 flex-shrink-0"
              title="Use my current location"
            >
              {gettingLocation ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Navigation size={18} />
              )}
            </Button>
          </div>

          {/* Map Container */}
          <div
            ref={mapContainerRef}
            className="w-full h-[200px] rounded-lg border border-surface-200 overflow-hidden"
            style={{ position: "relative", zIndex: 1 }}
          />

          {/* Instructions */}
          {/* <div className="text-sm text-surface-600 bg-surface-50 p-3 rounded-lg">
            💡 <strong>Tip:</strong> Search for an address above, click on the
            map, or drag the marker to select your exact location, then click
            &quot;Find Restaurants&quot;.
          </div> */}

          {/* Location Info & Action - Only one button */}
          {selectedLocation && (
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 bg-surface-100 rounded-lg">
              <div className="flex-1">
                <p className="text-sm font-medium text-surface-900">
                  {currentAddress || "Custom location"}
                </p>
                <p className="text-xs text-surface-600">
                  📍 {selectedLocation.lat.toFixed(5)},{" "}
                  {selectedLocation.lng.toFixed(5)}
                </p>
              </div>

              {/* Only one button - Find Restaurants */}
              <Button
                onClick={handleFindRestaurants}
                disabled={isLoading}
                className="bg-brand-primary hover:bg-brand-primary/90 flex-shrink-0"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={18} className="mr-2 animate-spin" />
                    Finding restaurants...
                  </>
                ) : (
                  <>
                    <Search size={18} className="mr-2" />
                    Find Restaurants
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}