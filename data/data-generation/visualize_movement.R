# Load necessary libraries
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

# Plot the movements of the selected residents
ggplot(filtered_schedules, aes(x = start, y = place, group = resident_id, color = as.factor(resident_id))) +
  geom_line(size = 1) +
  geom_point(size = 3) +
  labs(title = "Movement of Selected Residents",
       x = "Time (minutes since midnight)",
       y = "Place ID",
       color = "Resident ID") +
  theme_minimal()
