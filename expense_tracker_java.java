/**
 * Smart Expense Tracker - Java Spring Boot Version
 * Demonstrates Java REST API, ML-like algorithms, and modern design patterns
 */

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import java.util.*;
import java.util.stream.Collectors;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@SpringBootApplication
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ExpenseTracker {

    // In-memory storage (can be replaced with database)
    private List<Expense> expenses = new ArrayList<>();
    private Map<String, Double> budgets = new HashMap<>();
    private int expenseIdCounter = 1;

    // Category keywords for AI-like categorization
    private static final Map<String, List<String>> CATEGORY_KEYWORDS = new HashMap<>() {{
        put("food", Arrays.asList("restaurant", "cafe", "food", "pizza", "lunch", "dinner"));
        put("transport", Arrays.asList("uber", "lyft", "gas", "fuel", "parking", "taxi"));
        put("shopping", Arrays.asList("amazon", "walmart", "store", "shop", "clothing"));
        put("entertainment", Arrays.asList("netflix", "spotify", "movie", "cinema", "game"));
        put("utilities", Arrays.asList("electricity", "water", "internet", "phone", "bill"));
        put("health", Arrays.asList("pharmacy", "hospital", "doctor", "gym", "fitness"));
    }};

    public static void main(String[] args) {
        SpringApplication.run(ExpenseTracker.class, args);
        System.out.println("💰 Smart Expense Tracker API Started!");
        System.out.println("🚀 Server running on http://localhost:8080");
    }

    // ============= MODELS =============
    
    static class Expense {
        private int id;
        private double amount;
        private String description;
        private String category;
        private LocalDateTime date;
        private String notes;

        // Constructor
        public Expense(int id, double amount, String description, String category, String notes) {
            this.id = id;
            this.amount = amount;
            this.description = description;
            this.category = category;
            this.date = LocalDateTime.now();
            this.notes = notes;
        }

        // Getters and Setters
        public int getId() { return id; }
        public double getAmount() { return amount; }
        public String getDescription() { return description; }
        public String getCategory() { return category; }
        public LocalDateTime getDate() { return date; }
        public String getDateString() { 
            return date.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME); 
        }
        public String getNotes() { return notes; }
    }

    static class ExpenseRequest {
        private double amount;
        private String description;
        private String category;
        private String notes;

        // Getters and Setters
        public double getAmount() { return amount; }
        public void setAmount(double amount) { this.amount = amount; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public String getNotes() { return notes; }
        public void setNotes(String notes) { this.notes = notes; }
    }

    // ============= HELPER METHODS =============

    /**
     * Smart categorization using keyword matching
     */
    private String smartCategorize(String description) {
        String lowerDesc = description.toLowerCase();
        
        for (Map.Entry<String, List<String>> entry : CATEGORY_KEYWORDS.entrySet()) {
            for (String keyword : entry.getValue()) {
                if (lowerDesc.contains(keyword)) {
                    return entry.getKey();
                }
            }
        }
        return "other";
    }

    /**
     * Predict next month spending using statistical analysis
     */
    private double predictNextMonthSpending() {
        if (expenses.isEmpty()) {
            return 0.0;
        }

        // Group by month and calculate averages
        Map<String, Double> monthlyTotals = new HashMap<>();
        
        for (Expense exp : expenses) {
            String monthKey = exp.getDate().format(DateTimeFormatter.ofPattern("yyyy-MM"));
            monthlyTotals.put(monthKey, monthlyTotals.getOrDefault(monthKey, 0.0) + exp.getAmount());
        }

        // Calculate average
        double average = monthlyTotals.values().stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElse(0.0);

        // Apply trend analysis
        if (monthlyTotals.size() >= 3) {
            List<Double> sortedTotals = new ArrayList<>(monthlyTotals.values());
            double recentAvg = sortedTotals.subList(Math.max(0, sortedTotals.size() - 3), sortedTotals.size())
                .stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(average);
            
            double trend = (recentAvg - average) * 0.3;
            return Math.round((average + trend) * 100.0) / 100.0;
        }

        return Math.round(average * 100.0) / 100.0;
    }

    /**
     * Generate intelligent insights from spending data
     */
    private List<Map<String, String>> generateInsights() {
        List<Map<String, String>> insights = new ArrayList<>();

        if (expenses.isEmpty()) {
            return insights;
        }

        // Category analysis
        Map<String, Double> categoryTotals = expenses.stream()
            .collect(Collectors.groupingBy(
                Expense::getCategory,
                Collectors.summingDouble(Expense::getAmount)
            ));

        double totalSpent = categoryTotals.values().stream().mapToDouble(Double::doubleValue).sum();

        // Top spending category
        Map.Entry<String, Double> topCategory = categoryTotals.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .orElse(null);

        if (topCategory != null) {
            double percentage = (topCategory.getValue() / totalSpent) * 100;
            Map<String, String> insight = new HashMap<>();
            insight.put("type", "category_insight");
            insight.put("message", String.format("Your highest spending is on %s ($%.2f, %.1f%% of total)", 
                topCategory.getKey(), topCategory.getValue(), percentage));
            insight.put("icon", "📊");
            insights.add(insight);
        }

        // Recent spending trend
        LocalDateTime weekAgo = LocalDateTime.now().minusDays(7);
        double recentTotal = expenses.stream()
            .filter(exp -> exp.getDate().isAfter(weekAgo))
            .mapToDouble(Expense::getAmount)
            .sum();

        Map<String, String> trendInsight = new HashMap<>();
        trendInsight.put("type", "trend");
        trendInsight.put("message", String.format("You've spent $%.2f this week ($%.2f/day average)", 
            recentTotal, recentTotal / 7));
        trendInsight.put("icon", "📈");
        insights.add(trendInsight);

        return insights;
    }

    // ============= API ENDPOINTS =============

    @GetMapping("/")
    public Map<String, Object> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("name", "Smart Expense Tracker API");
        response.put("version", "1.0");
        response.put("language", "Java Spring Boot");
        response.put("features", Arrays.asList(
            "AI-powered auto-categorization",
            "Predictive analytics",
            "Budget tracking",
            "Smart insights"
        ));
        return response;
    }

    @PostMapping("/expense")
    public ResponseEntity<Map<String, Object>> addExpense(@RequestBody ExpenseRequest request) {
        // Validation
        if (request.getAmount() <= 0 || request.getDescription() == null || request.getDescription().isEmpty()) {
            return ResponseEntity.badRequest().body(
                Map.of("error", "Amount must be positive and description is required")
            );
        }

        // Auto-categorize if not provided
        String category = (request.getCategory() == null || request.getCategory().isEmpty()) 
            ? smartCategorize(request.getDescription())
            : request.getCategory();

        // Create expense
        Expense expense = new Expense(
            expenseIdCounter++,
            request.getAmount(),
            request.getDescription(),
            category,
            request.getNotes()
        );

        expenses.add(expense);

        // Check budget
        String budgetAlert = null;
        if (budgets.containsKey(category)) {
            double categoryTotal = expenses.stream()
                .filter(e -> e.getCategory().equals(category))
                .mapToDouble(Expense::getAmount)
                .sum();
            
            double budget = budgets.get(category);
            double percentage = (categoryTotal / budget) * 100;
            
            if (percentage >= 90) {
                budgetAlert = String.format("Budget alert: %.1f%% of %s budget used ($%.2f/$%.2f)",
                    percentage, category, categoryTotal, budget);
            }
        }

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("expense", Map.of(
            "id", expense.getId(),
            "amount", expense.getAmount(),
            "description", expense.getDescription(),
            "category", expense.getCategory(),
            "date", expense.getDateString()
        ));
        response.put("auto_categorized", request.getCategory() == null || request.getCategory().isEmpty());
        if (budgetAlert != null) {
            response.put("budget_alert", budgetAlert);
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/expenses")
    public Map<String, Object> getExpenses(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate) {
        
        List<Expense> filteredExpenses = new ArrayList<>(expenses);

        // Filter by category
        if (category != null && !category.isEmpty()) {
            filteredExpenses = filteredExpenses.stream()
                .filter(exp -> exp.getCategory().equals(category))
                .collect(Collectors.toList());
        }

        // Calculate summary
        double total = filteredExpenses.stream().mapToDouble(Expense::getAmount).sum();
        
        Map<String, Double> byCategory = filteredExpenses.stream()
            .collect(Collectors.groupingBy(
                Expense::getCategory,
                Collectors.summingDouble(Expense::getAmount)
            ));

        Map<String, Object> response = new HashMap<>();
        response.put("expenses", filteredExpenses.stream().map(exp -> Map.of(
            "id", exp.getId(),
            "amount", exp.getAmount(),
            "description", exp.getDescription(),
            "category", exp.getCategory(),
            "date", exp.getDateString()
        )).collect(Collectors.toList()));
        
        response.put("summary", Map.of(
            "total", Math.round(total * 100.0) / 100.0,
            "count", filteredExpenses.size(),
            "by_category", byCategory
        ));

        return response;
    }

    @GetMapping("/analytics")
    public Map<String, Object> getAnalytics() {
        if (expenses.isEmpty()) {
            return Map.of("message", "No expenses yet");
        }

        double totalSpent = expenses.stream().mapToDouble(Expense::getAmount).sum();
        double avgExpense = totalSpent / expenses.size();

        Map<String, Double> byCategory = expenses.stream()
            .collect(Collectors.groupingBy(
                Expense::getCategory,
                Collectors.summingDouble(Expense::getAmount)
            ));

        Map<String, Object> categorySummary = new HashMap<>();
        for (Map.Entry<String, Double> entry : byCategory.entrySet()) {
            long count = expenses.stream().filter(e -> e.getCategory().equals(entry.getKey())).count();
            categorySummary.put(entry.getKey(), Map.of(
                "total", Math.round(entry.getValue() * 100.0) / 100.0,
                "count", count,
                "percentage", Math.round((entry.getValue() / totalSpent) * 1000.0) / 10.0
            ));
        }

        return Map.of(
            "overall", Map.of(
                "total_spent", Math.round(totalSpent * 100.0) / 100.0,
                "total_transactions", expenses.size(),
                "average_expense", Math.round(avgExpense * 100.0) / 100.0
            ),
            "by_category", categorySummary
        );
    }

    @GetMapping("/insights")
    public Map<String, Object> getInsights() {
        return Map.of(
            "insights", generateInsights(),
            "generated_at", LocalDateTime.now().toString()
        );
    }

    @GetMapping("/predict")
    public Map<String, Object> predictSpending() {
        double prediction = predictNextMonthSpending();
        
        String confidence = expenses.size() > 30 ? "high" : 
                          expenses.size() > 10 ? "medium" : "low";

        return Map.of(
            "prediction", Map.of(
                "total", prediction,
                "confidence", confidence,
                "based_on_transactions", expenses.size()
            ),
            "recommendation", String.format("Based on your spending patterns, budget $%.2f to be safe", 
                prediction * 1.1)
        );
    }

    @PostMapping("/budget")
    public Map<String, Object> setBudget(@RequestBody Map<String, Object> request) {
        String category = (String) request.get("category");
        Double amount = ((Number) request.get("amount")).doubleValue();

        if (category == null || amount == null || amount <= 0) {
            return Map.of("error", "Category and positive amount are required");
        }

        budgets.put(category, amount);

        return Map.of(
            "success", true,
            "message", String.format("Budget set for %s: $%.2f", category, amount)
        );
    }

    @DeleteMapping("/expense/{id}")
    public ResponseEntity<Map<String, Object>> deleteExpense(@PathVariable int id) {
        boolean removed = expenses.removeIf(exp -> exp.getId() == id);

        if (!removed) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(Map.of("error", "Expense not found"));
        }

        return ResponseEntity.ok(Map.of(
            "success", true,
            "message", "Expense deleted"
        ));
    }
}