import numpy as np
from scipy.stats import linregress, skew, kurtosis, norm
from utils.db_conn import get_db_connection


def get_class_scores(class_id):
    # Returns list of (student_id, score, assessment_score) for regression
    with get_db_connection().cursor() as cursor:
        cursor.execute(
            """
            SELECT sc.student_id, ss.score, ss.assessment_id
            FROM student_classes sc
            JOIN student_scores ss ON sc.student_id = ss.student_id
            WHERE sc.class_id = %s
        """,
            (class_id,),
        )
        rows = cursor.fetchall()
    return rows


def get_class_advanced_stats(class_id):
    rows = get_class_scores(class_id)
    scores = [row["score"] for row in rows if row["score"] is not None]
    student_ids = [row["student_id"] for row in rows if row["score"] is not None]
    # Standard deviation
    std_dev = float(np.std(scores)) if scores else None
    # Outlier detection (2 std dev from mean)
    mean = float(np.mean(scores)) if scores else None
    outliers = (
        [student_ids[i] for i, s in enumerate(scores) if abs(s - mean) > 2 * std_dev]
        if scores and std_dev
        else []
    )
    # Regression: assessment_id as x, score as y (if multiple assessments)
    assessment_scores = {}
    for row in rows:
        aid = row["assessment_id"]
        if aid not in assessment_scores:
            assessment_scores[aid] = []
        assessment_scores[aid].append(row["score"])
    # Use mean score per assessment for regression
    x = []
    y = []
    for aid, scores_list in assessment_scores.items():
        x.append(aid)
        y.append(np.mean(scores_list))
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        regression = {
            "slope": round(slope, 4),
            "intercept": round(intercept, 2),
            "r2": round(r_value**2, 4),
        }
    else:
        regression = None
    return {
        "std_dev": round(std_dev, 2) if std_dev is not None else None,
        "outlier_count": len(outliers),
        "outliers": outliers,
        "regression": regression,
    }


def calculate_performance_trends(class_id):
    """Calculate performance trends including skewness, kurtosis, and quartile analysis"""
    rows = get_class_scores(class_id)
    scores = [row["score"] for row in rows if row["score"] is not None]

    if not scores or len(scores) < 3:
        return None

    # Basic statistics
    mean_score = float(np.mean(scores))
    median_score = float(np.median(scores))
    std_dev = float(np.std(scores))

    # Advanced distribution metrics
    skewness = float(skew(scores))
    kurt = float(kurtosis(scores))

    # Quartile analysis
    q1 = float(np.percentile(scores, 25))
    q3 = float(np.percentile(scores, 75))
    iqr = q3 - q1

    # Performance bands
    top_performers = len([s for s in scores if s >= q3 + 1.5 * iqr])
    middle_performers = len([s for s in scores if q1 - 1.5 * iqr <= s < q3 + 1.5 * iqr])
    bottom_performers = len([s for s in scores if s < q1 - 1.5 * iqr])

    # Performance consistency
    cv = (std_dev / mean_score) * 100 if mean_score > 0 else 0

    return {
        "mean": round(mean_score, 2),
        "median": round(median_score, 2),
        "skewness": round(skewness, 3),
        "kurtosis": round(kurt, 3),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "top_performers": top_performers,
        "middle_performers": middle_performers,
        "bottom_performers": bottom_performers,
        "coefficient_of_variation": round(cv, 2),
        "performance_distribution": {
            "top_percentage": round((top_performers / len(scores)) * 100, 1),
            "middle_percentage": round((middle_performers / len(scores)) * 100, 1),
            "bottom_percentage": round((bottom_performers / len(scores)) * 100, 1),
        },
    }


def calculate_assessment_difficulty_analysis(class_id):
    """Analyze assessment difficulty and student performance patterns"""
    with get_db_connection().cursor() as cursor:
        # Get all assessments and their scores for this class
        cursor.execute(
            """
            SELECT ga.id, ga.name, ga.max_score, ss.score, ss.student_id
            FROM grade_assessments ga
            JOIN student_scores ss ON ga.id = ss.assessment_id
            JOIN grade_subcategories gsc ON ga.subcategory_id = gsc.id
            JOIN grade_categories gc ON gsc.category_id = gc.id
            JOIN grade_structures gs ON gc.structure_id = gs.id
            WHERE gs.class_id = %s
            ORDER BY ga.created_at
        """,
            (class_id,),
        )
        assessment_data = cursor.fetchall()

    if not assessment_data:
        return None

    # Group by assessment
    assessments = {}
    for row in assessment_data:
        assessment_id = row["id"]
        if assessment_id not in assessments:
            assessments[assessment_id] = {
                "name": row["name"],
                "max_score": row["max_score"],
                "scores": [],
                "student_scores": {},
            }
        assessments[assessment_id]["scores"].append(row["score"])
        assessments[assessment_id]["student_scores"][row["student_id"]] = row["score"]

    # Calculate difficulty metrics for each assessment
    assessment_analytics = []
    for assessment_id, data in assessments.items():
        scores = data["scores"]
        if len(scores) < 3:
            continue

        mean_score = np.mean(scores)
        std_score = np.std(scores)
        median_score = np.median(scores)

        # Calculate difficulty index (0-100, where higher = more difficult)
        difficulty_index = 100 - ((mean_score / data["max_score"]) * 100)

        # Calculate discrimination index (difference between top and bottom performers)
        sorted_scores = sorted(scores, reverse=True)
        top_27 = sorted_scores[: int(len(sorted_scores) * 0.27)]
        bottom_27 = sorted_scores[-int(len(sorted_scores) * 0.27) :]

        top_avg = np.mean(top_27) if top_27 else 0
        bottom_avg = np.mean(bottom_27) if bottom_27 else 0
        discrimination_index = top_avg - bottom_avg

        # Calculate reliability (consistency of performance)
        reliability = std_score / data["max_score"] if data["max_score"] > 0 else 0

        assessment_analytics.append(
            {
                "assessment_id": assessment_id,
                "name": data["name"],
                "mean_score": round(mean_score, 2),
                "median_score": round(median_score, 2),
                "std_score": round(std_score, 2),
                "difficulty_index": round(difficulty_index, 1),
                "discrimination_index": round(discrimination_index, 2),
                "reliability": round(reliability, 3),
                "pass_rate": round(
                    (
                        len([s for s in scores if s >= data["max_score"] * 0.6])
                        / len(scores)
                    )
                    * 100,
                    1,
                ),
            }
        )

    # Overall class difficulty metrics
    if assessment_analytics:
        avg_difficulty = np.mean([a["difficulty_index"] for a in assessment_analytics])
        avg_discrimination = np.mean(
            [a["discrimination_index"] for a in assessment_analytics]
        )
        avg_reliability = np.mean([a["reliability"] for a in assessment_analytics])

        return {
            "assessment_analytics": assessment_analytics,
            "class_metrics": {
                "average_difficulty": round(avg_difficulty, 1),
                "average_discrimination": round(avg_discrimination, 2),
                "average_reliability": round(avg_reliability, 3),
                "assessment_count": len(assessment_analytics),
                "difficulty_range": f"{min([a['difficulty_index'] for a in assessment_analytics]):.1f} - {max([a['difficulty_index'] for a in assessment_analytics]):.1f}",
            },
        }
    return None


def calculate_learning_progress_analysis(class_id):
    """Analyze student learning progress and predict future performance"""
    rows = get_class_scores(class_id)

    if not rows or len(rows) < 5:
        return None

    # Group scores by student
    student_scores = {}
    for row in rows:
        student_id = row["student_id"]
        assessment_id = row["assessment_id"]
        score = row["score"]

        if student_id not in student_scores:
            student_scores[student_id] = {"scores": [], "assessments": []}
        student_scores[student_id]["scores"].append(score)
        student_scores[student_id]["assessments"].append(assessment_id)

    # Calculate progress metrics for each student
    student_progress = []
    for student_id, data in student_scores.items():
        if len(data["scores"]) < 2:
            continue

        scores = data["scores"]
        assessments = data["assessments"]

        # Calculate progress metrics
        first_score = scores[0]
        last_score = scores[-1]
        score_change = last_score - first_score
        percent_change = (score_change / first_score) * 100 if first_score > 0 else 0

        # Calculate trend (simple linear regression)
        x = np.arange(len(scores))
        y = np.array(scores)
        slope, intercept = np.polyfit(x, y, 1)

        # Calculate consistency
        std_dev = np.std(scores)
        cv = (std_dev / np.mean(scores)) * 100 if np.mean(scores) > 0 else 0

        # Predict next assessment score
        predicted_next = slope * len(scores) + intercept

        student_progress.append(
            {
                "student_id": student_id,
                "score_count": len(scores),
                "first_score": round(first_score, 2),
                "last_score": round(last_score, 2),
                "score_change": round(score_change, 2),
                "percent_change": round(percent_change, 1),
                "trend_slope": round(slope, 3),
                "consistency_cv": round(cv, 1),
                "predicted_next_score": round(predicted_next, 2),
                "improvement_trend": (
                    "improving" if slope > 0 else "declining" if slope < 0 else "stable"
                ),
            }
        )

    # Calculate class-wide progress metrics
    if student_progress:
        improving_students = len(
            [s for s in student_progress if s["improvement_trend"] == "improving"]
        )
        declining_students = len(
            [s for s in student_progress if s["improvement_trend"] == "declining"]
        )
        stable_students = len(
            [s for s in student_progress if s["improvement_trend"] == "stable"]
        )

        avg_progress = np.mean([s["percent_change"] for s in student_progress])
        avg_consistency = np.mean([s["consistency_cv"] for s in student_progress])

        return {
            "student_progress": student_progress,
            "class_progress_metrics": {
                "total_students_analyzed": len(student_progress),
                "improving_students": improving_students,
                "declining_students": declining_students,
                "stable_students": stable_students,
                "average_progress_percentage": round(avg_progress, 1),
                "average_consistency": round(avg_consistency, 1),
                "improving_percentage": round(
                    (improving_students / len(student_progress)) * 100, 1
                ),
                "declining_percentage": round(
                    (declining_students / len(student_progress)) * 100, 1
                ),
                "stable_percentage": round(
                    (stable_students / len(student_progress)) * 100, 1
                ),
            },
        }
    return None


def get_comprehensive_class_analytics(class_id):
    """Get comprehensive analytics including all advanced metrics"""
    basic_stats = get_class_advanced_stats(class_id)
    performance_trends = calculate_performance_trends(class_id)
    difficulty_analysis = calculate_assessment_difficulty_analysis(class_id)
    progress_analysis = calculate_learning_progress_analysis(class_id)

    return {
        "basic_statistics": basic_stats,
        "performance_trends": performance_trends,
        "difficulty_analysis": difficulty_analysis,
        "progress_analysis": progress_analysis,
    }


def calculate_correlation_analysis(class_id):
    """Analyze correlations between different assessment types and performance factors"""
    rows = get_class_scores(class_id)

    if not rows or len(rows) < 10:
        return None

    # Group by student and assessment
    student_assessment_data = {}
    for row in rows:
        student_id = row["student_id"]
        assessment_id = row["assessment_id"]
        score = row["score"]

        if student_id not in student_assessment_data:
            student_assessment_data[student_id] = {"assessments": {}, "scores": []}
        student_assessment_data[student_id]["assessments"][assessment_id] = score
        student_assessment_data[student_id]["scores"].append(score)

    # Calculate correlation metrics
    if len(student_assessment_data) < 3:
        return None

    # Prepare data for correlation analysis
    assessment_ids = set()
    student_scores = []

    for student_id, data in student_assessment_data.items():
        if len(data["assessments"]) > 1:
            assessment_ids.update(data["assessments"].keys())
            student_scores.append(
                {
                    "student_id": student_id,
                    "assessments": data["assessments"],
                    "overall_performance": np.mean(list(data["assessments"].values())),
                }
            )

    if len(assessment_ids) < 2:
        return None

    # Convert to matrix for correlation analysis
    assessment_ids = sorted(list(assessment_ids))
    correlation_matrix = np.zeros((len(assessment_ids), len(assessment_ids)))
    assessment_names = []

    # Get assessment names
    with get_db_connection().cursor() as cursor:
        placeholders = ",".join(["%s"] * len(assessment_ids))
        cursor.execute(
            f"""
            SELECT id, name FROM grade_assessments
            WHERE id IN ({placeholders})
        """,
            tuple(assessment_ids),
        )
        assessment_info = {row["id"]: row["name"] for row in cursor.fetchall()}

    # Build correlation matrix
    for i, aid1 in enumerate(assessment_ids):
        assessment_names.append(assessment_info.get(aid1, f"Assessment {aid1}"))
        scores1 = []
        scores2_list = [[] for _ in range(len(assessment_ids))]

        for student in student_scores:
            if aid1 in student["assessments"]:
                scores1.append(student["assessments"][aid1])
                for j, aid2 in enumerate(assessment_ids):
                    if aid2 in student["assessments"]:
                        scores2_list[j].append(student["assessments"][aid2])

        for j, aid2 in enumerate(assessment_ids):
            if i == j:
                correlation_matrix[i, j] = 1.0
            else:
                scores2 = scores2_list[j]
                if len(scores1) > 1 and len(scores2) > 1:
                    correlation_matrix[i, j] = np.corrcoef(scores1, scores2)[0, 1]
                else:
                    correlation_matrix[i, j] = 0.0

    # Calculate overall class correlation metrics
    upper_triangle = correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)]
    valid_correlations = upper_triangle[~np.isnan(upper_triangle)]

    return {
        "correlation_matrix": correlation_matrix.tolist(),
        "assessment_names": assessment_names,
        "correlation_metrics": {
            "average_correlation": (
                round(float(np.mean(valid_correlations)), 3)
                if len(valid_correlations) > 0
                else None
            ),
            "max_correlation": (
                round(float(np.max(valid_correlations)), 3)
                if len(valid_correlations) > 0
                else None
            ),
            "min_correlation": (
                round(float(np.min(valid_correlations)), 3)
                if len(valid_correlations) > 0
                else None
            ),
            "high_correlation_count": len([c for c in valid_correlations if c > 0.7]),
            "moderate_correlation_count": len(
                [c for c in valid_correlations if 0.4 <= c <= 0.7]
            ),
            "low_correlation_count": len([c for c in valid_correlations if c < 0.4]),
        },
        "interpretation": {
            "high_correlation_assessments": "Assessments with correlation > 0.7 suggest they may be measuring similar skills or concepts",
            "moderate_correlation_assessments": "Assessments with correlation 0.4-0.7 suggest some relationship but different focus areas",
            "low_correlation_assessments": "Assessments with correlation < 0.4 suggest they measure distinct skills or have different difficulty levels",
        },
    }


def calculate_grade_distribution_analysis(class_id):
    """Analyze grade distribution patterns and predict grade outcomes"""
    rows = get_class_scores(class_id)
    scores = [row["score"] for row in rows if row["score"] is not None]

    if not scores or len(scores) < 5:
        return None

    # Calculate grade distribution metrics
    mean_score = np.mean(scores)
    std_score = np.std(scores)

    # Fit normal distribution
    mu, sigma = norm.fit(scores)

    # Calculate percentile ranks
    percentiles = np.percentile(scores, [10, 25, 50, 75, 90])
    grade_bands = {
        "bottom_10": round(percentiles[0], 2),
        "lower_quartile": round(percentiles[1], 2),
        "median": round(percentiles[2], 2),
        "upper_quartile": round(percentiles[3], 2),
        "top_10": round(percentiles[4], 2),
    }

    # Calculate grade distribution
    def categorize_score(score):
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for score in scores:
        grade = categorize_score(score)
        grade_counts[grade] += 1

    # Calculate expected vs actual distribution
    expected_distribution = {
        "A": round(len(scores) * 0.20),  # Top 20%
        "B": round(len(scores) * 0.25),  # Next 25%
        "C": round(len(scores) * 0.30),  # Middle 30%
        "D": round(len(scores) * 0.15),  # Next 15%
        "F": round(len(scores) * 0.10),  # Bottom 10%
    }

    # Calculate grade prediction confidence
    confidence_scores = []
    for score in scores:
        # Calculate how typical this score is based on distribution
        z_score = (score - mu) / sigma
        confidence = 1 - abs(norm.cdf(z_score) - 0.5)  # Higher when closer to mean
        confidence_scores.append(confidence)

    avg_confidence = np.mean(confidence_scores)

    return {
        "distribution_metrics": {
            "mean": round(mean_score, 2),
            "std_dev": round(std_score, 2),
            "normal_distribution_fit": {"mu": round(mu, 2), "sigma": round(sigma, 2)},
            "grade_bands": grade_bands,
        },
        "grade_distribution": {
            "actual": {grade: count for grade, count in grade_counts.items()},
            "expected": expected_distribution,
            "deviations": {
                grade: grade_counts[grade] - expected_distribution[grade]
                for grade in grade_counts
            },
        },
        "distribution_quality": {
            "average_confidence": round(float(avg_confidence), 3),
            "distribution_evenness": (
                round(float(std_score / mean_score), 3) if mean_score > 0 else None
            ),
            "outlier_percentage": round(
                float(
                    len([s for s in scores if abs(s - mu) > 2 * sigma])
                    / len(scores)
                    * 100
                ),
                1,
            ),
        },
        "interpretation": {
            "distribution_shape": (
                "Normal"
                if abs(skew(scores)) < 0.5
                else "Skewed Right" if skew(scores) > 0 else "Skewed Left"
            ),
            "grade_spread": (
                "Wide"
                if std_score > mean_score * 0.3
                else "Moderate" if std_score > mean_score * 0.15 else "Narrow"
            ),
            "prediction_reliability": (
                "High"
                if avg_confidence > 0.8
                else "Moderate" if avg_confidence > 0.6 else "Low"
            ),
        },
    }


def calculate_risk_analysis(class_id):
    """Identify students at risk and predict intervention needs"""
    rows = get_class_scores(class_id)

    if not rows or len(rows) < 3:
        return None

    # Group by student
    student_data = {}
    for row in rows:
        student_id = row["student_id"]
        assessment_id = row["assessment_id"]
        score = row["score"]

        if student_id not in student_data:
            student_data[student_id] = {"scores": [], "assessments": []}
        student_data[student_id]["scores"].append(score)
        student_data[student_id]["assessments"].append(assessment_id)

    # Calculate risk metrics for each student
    risk_assessments = []
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0

    for student_id, data in student_data.items():
        if len(data["scores"]) < 2:
            continue

        scores = data["scores"]

        # Calculate risk factors
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        current_score = scores[-1]  # Most recent score
        trend = np.polyfit(np.arange(len(scores)), scores, 1)[0]  # Slope

        # Calculate risk score (0-100)
        risk_score = 0

        # Current performance factor
        if current_score < 60:
            risk_score += 40
        elif current_score < 70:
            risk_score += 20
        elif current_score < 80:
            risk_score += 10

        # Trend factor
        if trend < -2:
            risk_score += 30
        elif trend < -1:
            risk_score += 15
        elif trend < 0:
            risk_score += 5

        # Consistency factor
        cv = (std_score / mean_score) * 100 if mean_score > 0 else 0
        if cv > 30:
            risk_score += 20
        elif cv > 20:
            risk_score += 10
        elif cv > 10:
            risk_score += 5

        # Determine risk level
        if risk_score >= 60:
            risk_level = "High"
            high_risk_count += 1
        elif risk_score >= 30:
            risk_level = "Medium"
            medium_risk_count += 1
        else:
            risk_level = "Low"
            low_risk_count += 1

        # Predict final grade based on current trend
        predicted_final = current_score + trend * 2  # Extrapolate 2 assessments ahead
        predicted_final = max(0, min(100, predicted_final))  # Clamp to 0-100

        risk_assessments.append(
            {
                "student_id": student_id,
                "current_score": round(current_score, 2),
                "mean_score": round(mean_score, 2),
                "trend": round(trend, 3),
                "consistency_cv": round(cv, 1),
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level,
                "predicted_final": round(predicted_final, 2),
                "recommended_action": get_risk_recommendation(
                    risk_level, current_score, trend
                ),
            }
        )

    # Calculate class risk metrics
    total_students = len(risk_assessments)
    high_risk_percentage = (
        (high_risk_count / total_students) * 100 if total_students > 0 else 0
    )
    medium_risk_percentage = (
        (medium_risk_count / total_students) * 100 if total_students > 0 else 0
    )
    low_risk_percentage = (
        (low_risk_count / total_students) * 100 if total_students > 0 else 0
    )

    return {
        "risk_assessments": risk_assessments,
        "class_risk_metrics": {
            "total_students_analyzed": total_students,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "high_risk_percentage": round(high_risk_percentage, 1),
            "medium_risk_percentage": round(medium_risk_percentage, 1),
            "low_risk_percentage": round(low_risk_percentage, 1),
            "average_risk_score": round(
                np.mean([r["risk_score"] for r in risk_assessments]), 1
            ),
        },
        "intervention_recommendations": {
            "urgent_interventions": high_risk_count,
            "monitoring_needed": medium_risk_count,
            "on_track_students": low_risk_count,
            "priority_recommendation": get_class_intervention_recommendation(
                high_risk_percentage
            ),
        },
    }


def get_risk_recommendation(risk_level, current_score, trend):
    """Generate specific recommendations based on risk assessment"""
    if risk_level == "High":
        if current_score < 50 and trend < 0:
            return "URGENT: Student is struggling significantly and performance is declining. Immediate intervention required - consider one-on-one tutoring, modified assignments, and progress monitoring."
        elif current_score < 50:
            return "HIGH: Student is performing well below expectations. Recommend targeted support, additional practice, and frequent progress checks."
        else:
            return "HIGH: Student shows declining performance trend. Recommend identifying specific challenges and providing focused support."
    elif risk_level == "Medium":
        if trend < 0:
            return "MEDIUM: Student shows declining trend. Recommend monitoring closely and providing additional support if decline continues."
        else:
            return "MEDIUM: Student performance is borderline. Recommend encouragement and targeted practice in weaker areas."
    else:
        if trend > 0:
            return "LOW: Student is performing well with positive trend. Continue current approach and provide enrichment opportunities."
        else:
            return "LOW: Student is performing satisfactorily. Maintain current support level and monitor for changes."


def get_class_intervention_recommendation(high_risk_percentage):
    """Generate class-level intervention recommendations"""
    if high_risk_percentage >= 30:
        return "CRITICAL: Over 30% of students are at high risk. Immediate comprehensive intervention needed including curriculum review, teaching method assessment, and additional support resources."
    elif high_risk_percentage >= 20:
        return "SERIOUS: 20-30% of students are at high risk. Significant intervention required with targeted support programs and teaching strategy adjustments."
    elif high_risk_percentage >= 10:
        return "MODERATE: 10-20% of students are at high risk. Implement targeted intervention programs and monitor effectiveness."
    else:
        return "STABLE: Less than 10% of students are at high risk. Continue current monitoring and support approaches."


def get_comprehensive_class_analytics_v2(class_id):
    """Get comprehensive analytics including all advanced metrics"""
    basic_stats = get_class_advanced_stats(class_id)
    performance_trends = calculate_performance_trends(class_id)
    difficulty_analysis = calculate_assessment_difficulty_analysis(class_id)
    progress_analysis = calculate_learning_progress_analysis(class_id)
    correlation_analysis = calculate_correlation_analysis(class_id)
    grade_distribution = calculate_grade_distribution_analysis(class_id)
    risk_analysis = calculate_risk_analysis(class_id)

    return {
        "basic_statistics": basic_stats,
        "performance_trends": performance_trends,
        "difficulty_analysis": difficulty_analysis,
        "progress_analysis": progress_analysis,
        "correlation_analysis": correlation_analysis,
        "grade_distribution": grade_distribution,
        "risk_analysis": risk_analysis,
    }
