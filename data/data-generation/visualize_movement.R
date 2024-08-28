# Create a data frame that maps place IDs to place types
place_types <- data.frame(
  place = c(0:99, 100:104, 105:107, 108, 109, 110:112),
  type = c(rep("cell", 100), 
           rep("activity_room", 5), 
           rep("cafeteria", 3), 
           rep("outdoor_area", 1), 
           rep("medical", 1), 
           rep("administrative", 3))
)

# Merge the place types with the filtered schedules
filtered_schedules <- filtered_schedules %>%
  left_join(place_types, by = "place")

# Plot the movements of the selected residents with color-coded place types
ggplot(filtered_schedules, aes(x = start, y = as.factor(place), group = resident_id)) +
  geom_line(aes(color = type), size = 1) +
  geom_point(aes(color = type), size = 3) +
  labs(title = "Movement of Selected Residents",
       x = "Time (minutes since midnight)",
       y = "Place ID",
       color = "Place Type") +
  theme_minimal()
