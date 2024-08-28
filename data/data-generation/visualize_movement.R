library(ggplot2)
library(dplyr)

# Load the schedule data
schedules <- read.csv("schedule.csv")

# Select a few residents to visualize (e.g., first 3)
selected_residents <- schedules %>% filter(resident_id %in% c(0:9))

# Remove long vertical bars by focusing only on movements
filtered_schedules <- selected_residents %>%
  group_by(resident_id) %>%
  filter(place != lag(place, default = first(place))) %>%
  ungroup()

# Define y-axis ranges for each place type
place_type_ranges <- data.frame(
  type = c("cell", "activity_room", "cafeteria", "outdoor_area", "medical", "administrative"),
  ymin = c(0, 100, 105, 108, 109, 110),
  ymax = c(99, 104, 107, 108, 109, 112)
)

# Merge with the filtered schedules to get place types
filtered_schedules <- filtered_schedules %>%
  left_join(place_types, by = "place")

# Create the plot with shaded backgrounds
p1 <- 
ggplot() +
  geom_rect(data = place_type_ranges, aes(xmin = -Inf, xmax = Inf, ymin = ymin, ymax = ymax, fill = type), alpha = 0.1) +
  geom_line(data = filtered_schedules, aes(x = start, y = place, group = resident_id, color = as.factor(resident_id)), size = 1) +
  geom_point(data = filtered_schedules, aes(x = start, y = place, group = resident_id, color = as.factor(resident_id)), size = 3) +
  scale_fill_manual(values = c("lightblue", "lightgreen", "lightpink", "lightyellow", "lightgray", "lightcoral")) +
  labs(title = "Movement of Selected Residents",
       x = "Time (minutes since midnight)",
       y = "Place ID",
       fill = "Place Type",
       color = "Resident ID") +
  theme_minimal() +
  theme(legend.position = "right")

p1

p2 <- 
  # Create the plot with enhanced shaded backgrounds and labels
  ggplot() +
    geom_rect(data = place_type_ranges, aes(xmin = -Inf, xmax = Inf, ymin = ymin, ymax = ymax, fill = type), alpha = 0.2) +
    geom_line(data = filtered_schedules, aes(x = start, y = place, group = resident_id, color = as.factor(resident_id)), size = 1) +
    geom_point(data = filtered_schedules, aes(x = start, y = place, group = resident_id, color = as.factor(resident_id)), size = 3) +
    scale_fill_manual(values = c("lightblue", "lightgreen", "lightpink", "lightyellow", "lightgray", "lightcoral")) +
    labs(title = "Movement of Selected Residents",
        x = "Time (minutes since midnight)",
        y = "Place ID",
        fill = "Place Type",
        color = "Resident ID") +
    theme_minimal() +
    theme(legend.position = "right",
          axis.text.y = element_text(size = 10),
          plot.title = element_text(hjust = 0.5, size = 14)) +
    scale_y_continuous(breaks = place_type_ranges$ymin, labels = place_type_ranges$type)
p2