from typing import List, Dict, Any, Optional
import os
import pandas as pd
import numpy as np
from datetime import datetime

from db.client import DatabaseClient
from db.repositories import ParticipantRepository
from db.models import Participant

from core.logging import get_logger
from core.constants import Platform, Batch, College

logger = get_logger(__name__)

class LeaderboardService:
    """Service for generating comprehensive and visually appealing leaderboards"""
    # Display names for platforms and other columns
    COLUMN_DISPLAY_NAMES = {
        "Hall Ticket No": "Registration ID",
        "CodeChef": "CodeChef Score",
        "CodeForces": "CodeForces Score",
        "GeeksForGeeks": "GFG Score",
        "HackerRank": "HackerRank Score",
        "LeetCode": "LeetCode Score",
        "Total Rating": "Overall Score",
        "Percentile": "Performance Percentile",
        "Normalized Rating": "Normalized Score"
    }
    
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        """Initialize the service"""
        if db_client is None:
            logger.error("Database client is required")
            raise ValueError("Database client is required")
        self.db_client = db_client
        self.repository = ParticipantRepository(self.db_client)
        
    def generate_leaderboard(self, batch: Batch, college: College, output_path: str, include_charts: bool = True) -> str:
        """Generate a comprehensive leaderboard for a batch
        
        Args:
            batch (Batch): The batch to generate the leaderboard for
            college (College): The college to generate the leaderboard for
            output_path (str): Path to save the Excel file
            include_charts (bool): Whether to include charts in the Excel file
            
        Returns:
            str: Path to the generated Excel file
        """ 
        logger.info(f"Generating leaderboard for batch: {batch.name} at college: {college.name}")
        
        college_name, batch_num = college.name, batch.value
        
        # Get all participants
        participants = self.repository.get_all_participants(batch, college)
        
        if not participants:
            logger.warning(f"No participants found for batch: {batch.name}")
            raise ValueError(f"No participants found for batch: {batch.name}")
        
        logger.info(f"Retrieved {len(participants)} participants for leaderboard")
        
        # Convert to DataFrame
        df = self._participants_to_dataframe(participants)
        
        # Add normalized ratings across platforms
        df = self._normalize_ratings(df, college, batch)
        
        # Sort by total rating descending
        df = df.sort_values("Overall Score", ascending=False)
        
        # Add rank column
        df.insert(0, 'Rank', range(1, len(df) + 1))
        
        # Format date in output filename if not specified
        if output_path == "leaderboard.xlsx" or not output_path:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = os.path.dirname(output_path) if output_path else "."
            file_name = f"leaderboard_{college_name}_{batch_num}_{timestamp}.xlsx"
            output_path = os.path.join(output_dir, file_name)
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Generate Excel file with enhanced formatting
        self._generate_excel(df, output_path, f"{college_name} {batch_num} Competitive Programming Leaderboard", include_charts=True)
        
        logger.info(f"Enhanced leaderboard generated at: {output_path}")
        return output_path
        
    def _participants_to_dataframe(self, participants: List[Participant]) -> pd.DataFrame:
        """Convert participants to a DataFrame with improved column naming
        
        Args:
            participants (List[Participant]): List of participants
            
        Returns:
            pd.DataFrame: DataFrame with participant data and better column names
        """
        data = []
        for participant in participants:
            row = {
                "Registration ID": participant.hall_ticket_no,
                "Name": participant.name,
                "Batch": participant.batch.value,
                # Include platform scores
                "CodeChef Score": participant.platforms.get(Platform.CODECHEF.value).rating if participant.platforms.get(Platform.CODECHEF.value) else 0,
                "CodeForces Score": participant.platforms.get(Platform.CODEFORCES.value).rating if participant.platforms.get(Platform.CODEFORCES.value) else 0,
                "GFG Score": participant.platforms.get(Platform.GEEKSFORGEEKS.value).rating if participant.platforms.get(Platform.GEEKSFORGEEKS.value) else 0,
                "HackerRank Score": participant.platforms.get(Platform.HACKERRANK.value).rating if participant.platforms.get(Platform.HACKERRANK.value) else 0,
                "LeetCode Score": participant.platforms.get(Platform.LEETCODE.value).rating if participant.platforms.get(Platform.LEETCODE.value) else 0,
                # Add platform handles
                "CodeChef Handle": participant.platforms.get(Platform.CODECHEF.value).handle if participant.platforms.get(Platform.CODECHEF.value) else "",
                "CodeForces Handle": participant.platforms.get(Platform.CODEFORCES.value).handle if participant.platforms.get(Platform.CODEFORCES.value) else "",
                "GFG Handle": participant.platforms.get(Platform.GEEKSFORGEEKS.value).handle if participant.platforms.get(Platform.GEEKSFORGEEKS.value) else "",
                "HackerRank Handle": participant.platforms.get(Platform.HACKERRANK.value).handle if participant.platforms.get(Platform.HACKERRANK.value) else "",
                "LeetCode Handle": participant.platforms.get(Platform.LEETCODE.value).handle if participant.platforms.get(Platform.LEETCODE.value) else "",
                # Add existence status
                "CodeChef Exists": participant.platforms.get(Platform.CODECHEF.value).exists if participant.platforms.get(Platform.CODECHEF.value) else False,
                "CodeForces Exists": participant.platforms.get(Platform.CODEFORCES.value).exists if participant.platforms.get(Platform.CODEFORCES.value) else False,
                "GFG Exists": participant.platforms.get(Platform.GEEKSFORGEEKS.value).exists if participant.platforms.get(Platform.GEEKSFORGEEKS.value) else False,
                "HackerRank Exists": participant.platforms.get(Platform.HACKERRANK.value).exists if participant.platforms.get(Platform.HACKERRANK.value) else False,
                "LeetCode Exists": participant.platforms.get(Platform.LEETCODE.value).exists if participant.platforms.get(Platform.LEETCODE.value) else False,
                # Overall metrics
                "Overall Score": participant.total_rating,
                "Performance Percentile": participant.percentile
            }
            data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Fill NA values with 0
        df.fillna(0, inplace=True)
        
        # Format percentile to 2 decimal places
        if "Performance Percentile" in df.columns:
            df["Performance Percentile"] = df["Performance Percentile"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "0.00")
            
        return df
    
    def _normalize_ratings(self, df: pd.DataFrame, college: College, batch: Batch) -> pd.DataFrame:
        """Normalize platform ratings to a 0-100 scale
        
        Args:
            df (pd.DataFrame): DataFrame with participant data
            
        Returns:
            pd.DataFrame: DataFrame with normalized ratings
        """
        # Define platform columns and their corresponding Platform enum values
        platform_columns = {
            "CodeChef Score": Platform.CODECHEF.value,
            "CodeForces Score": Platform.CODEFORCES.value,
            "GFG Score": Platform.GEEKSFORGEEKS.value,
            "HackerRank Score": Platform.HACKERRANK.value,
            "LeetCode Score": Platform.LEETCODE.value
        }
        
        # Add normalized columns (0-100 scale)
        for col, platform in platform_columns.items():
            max_rating = self.repository.get_max_rating(Platform._value2member_map_[platform], college, batch)
            norm_col = f"Normalized {col}"
            
            # Get non-zero values for this platform
            non_zero_values = df[df[col] > 0][col]
            
            if len(non_zero_values) > 0:
                # Calculate min and max values for better scaling
                min_val = non_zero_values.min()
                # Use 95th percentile as effective max to handle outliers
                p95_val = np.percentile(non_zero_values, 95)
                
                # Normalize on 0-100 scale
                df[norm_col] = df[col].apply(
                    lambda x: min(100, max(0, (x / max_rating) * 100)) if x > 0 else 0
                )
            else:
                # If no non-zero values, just set to 0
                df[norm_col] = 0
                
        # Calculate a combined normalized score (average of all normalized platform scores)
        norm_cols = [f"Normalized {col}" for col in platform_columns.keys()]
        
        # Count how many platforms each participant is active on
        df["Active Platforms"] = (df[list(platform_columns.keys())] > 0).sum(axis=1)
        
        # Calculate normalized score as average of active platform scores
        df["Normalized Score"] = df.apply(
            lambda row: sum(row[norm_cols]) / max(1, row["Active Platforms"]), 
            axis=1
        )
        
        return df
    
    def _generate_excel(self, df: pd.DataFrame, output_path: str, title: str, include_charts: bool = True) -> None:
        """Generate an Excel file with enhanced formatting and visualizations
        
        Args:
            df (pd.DataFrame): DataFrame with participant data
            output_path (str): Path to save the Excel file
            title (str): Title of the leaderboard
            include_charts (bool): Whether to include charts in the Excel file
        """
        # Create Excel writer with pandas
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        
        # Write DataFrame to Excel
        df.to_excel(writer, sheet_name='Leaderboard', index=False, startrow=2)  # Start from row 2 to allow for title
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Leaderboard']
        
        # Add enhanced formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#2E7D32',  # Dark green
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 12
        })
        
        # Alternating row colors with improved colors
        even_row_format = workbook.add_format({
            'bg_color': '#F1F8E9',  # Very light green
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#E0E0E0'
        })
        
        odd_row_format = workbook.add_format({
            'bg_color': '#FFFFFF',  # White
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#E0E0E0'
        })
        
        # Format for top ranks with different colors
        gold_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FDD835',  # Gold
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 12
        })
        
        silver_format = workbook.add_format({
            'bold': True,
            'bg_color': '#BDBDBD',  # Silver
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 12
        })
        
        bronze_format = workbook.add_format({
            'bold': True,
            'bg_color': '#BF8970',  # Bronze
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 12
        })
        
        # Enhanced title format
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 18,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#2E7D32',  # Dark green
        })
        
        # Enhanced subtitle format
        subtitle_format = workbook.add_format({
            'italic': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#616161',  # Dark gray
        })
        
        # Number formats
        score_format = workbook.add_format({
            'num_format': '0.00',
            'align': 'center',
            'valign': 'vcenter'
        })
        
        percentage_format = workbook.add_format({
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Handle formats - green for existing, red for non-existing
        handle_exists_format = workbook.add_format({
            'font_color': '#2E7D32',  # Dark green
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        handle_not_exists_format = workbook.add_format({
            'font_color': '#C62828',  # Dark red
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Set column widths with better sizing
        worksheet.set_column('A:A', 6)    # Rank
        worksheet.set_column('B:B', 18)   # Registration ID (slightly wider for ID display)
        worksheet.set_column('C:C', 25)   # Name (increased for longer names)
        worksheet.set_column('D:D', 10)   # Batch (slightly wider)
        worksheet.set_column('E:I', 16)   # Platform scores (wider for score headers)
        worksheet.set_column('J:N', 22)   # Platform handles (wider for handle URLs)
        worksheet.set_column('O:S', 1)    # Platform existence status (hidden)
        worksheet.set_column('T:T', 18)   # Overall Score (wider for header)
        worksheet.set_column('U:U', 20)   # Performance Percentile (wider for long header)
        worksheet.set_column('V:AA', 25)  # Normalized scores (much wider for long headers)
        worksheet.set_column('AB:AB', 16) # Active Platforms
        worksheet.set_column('AC:AC', 18) # Normalized Score (wider for header)
        
        # Add title and subtitle
        worksheet.merge_range('A1:AC1', title, title_format)
        worksheet.merge_range('A2:AC2', f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}", subtitle_format)
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(2, col_num, value, header_format)
            
        # Apply formats to rows
        for row_num in range(3, len(df) + 3):
            # Get actual rank (adjust for header row offset)
            rank = df.iloc[row_num-3, 0]
            
            # Base format based on rank
            row_format = None
            if rank == 1:  # Gold
                row_format = gold_format
            elif rank == 2:  # Silver
                row_format = silver_format
            elif rank == 3:  # Bronze
                row_format = bronze_format
            # Apply alternating row formats
            elif row_num % 2 == 0:
                row_format = even_row_format
            else:
                row_format = odd_row_format
                
            # Apply format to columns
            for col_num in range(len(df.columns)):
                value = df.iloc[row_num-3, col_num]
                
                # Special formatting for handle columns based on existence status
                if 9 <= col_num <= 13:  # Handle columns
                    # Check if the corresponding existence status is True
                    exists_value = df.iloc[row_num-3, col_num + 5]  # +5 to get to the existence columns
                    if exists_value:
                        worksheet.write(row_num, col_num, value, handle_exists_format)
                    else:
                        worksheet.write(row_num, col_num, value, handle_not_exists_format)
                else:
                    # Use default row formatting for non-handle columns
                    worksheet.write(row_num, col_num, value, row_format)
        
        # Hide existence status columns (they're only used for coloring handles)
        for col in range(14, 19):  # Existence status columns O-S
            worksheet.set_column(col, col, None, None, {'hidden': True})
        
        # Add conditional formatting (green to red gradient for scores)
        # This makes high scores green and low scores red
        for col in range(4, 9):  # Platform score columns
            worksheet.conditional_format(3, col, len(df) + 2, col, {
                'type': '3_color_scale',
                'min_color': '#FFCDD2',  # Light red
                'mid_color': '#FFFDE7',  # Light yellow
                'max_color': '#C8E6C9',  # Light green
            })
            
        # Add conditional formatting for normalized scores
        for col in range(21, 28):  # Normalized score columns
            worksheet.conditional_format(3, col, len(df) + 2, col, {
                'type': '3_color_scale',
                'min_color': '#FFCDD2',  # Light red
                'mid_color': '#FFFDE7',  # Light yellow
                'max_color': '#C8E6C9',  # Light green
            })
        
        # Add timestamp
        timestamp_format = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'font_color': '#757575'  # Medium gray
        })
        
        # Add summary section
        summary_start_row = len(df) + 5
        platforms = ["CodeChef Score", "CodeForces Score", "GFG Score", "HackerRank Score", "LeetCode Score"]
        
        # Add headers for summary section
        summary_header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_color': '#2E7D32',
            'bottom': 1,
            'bottom_color': '#2E7D32'
        })
        
        worksheet.write(summary_start_row, 0, "Summary Statistics", summary_header_format)
        worksheet.merge_range(summary_start_row, 0, summary_start_row, 5, "Summary Statistics", summary_header_format)
        
        # Basic statistics
        stat_format = workbook.add_format({
            'font_size': 11,
            'align': 'left'
        })
        
        stat_value_format = workbook.add_format({
            'font_size': 11,
            'align': 'right',
            'bold': True
        })
        
        # Row for total participants
        worksheet.write(summary_start_row + 1, 0, "Total Participants:", stat_format)
        worksheet.write(summary_start_row + 1, 1, len(df), stat_value_format)
        
        # Platform statistics
        worksheet.write(summary_start_row + 2, 0, "Platform Participation:", stat_format)
        
        for i, platform in enumerate(platforms):
            count = (df[platform] > 0).sum()
            percentage = count / len(df) * 100
            worksheet.write(summary_start_row + 3 + i, 0, f"• {platform.split(' ')[0]}:", stat_format)
            worksheet.write(summary_start_row + 3 + i, 1, count, stat_format)
            worksheet.write(summary_start_row + 3 + i, 2, f"({percentage:.1f}%)", stat_format)
        
        # Average scores
        avg_row = summary_start_row + 9
        worksheet.write(avg_row, 0, "Average Scores:", stat_format)
        
        for i, platform in enumerate(platforms):
            non_zero_values = df[df[platform] > 0][platform]
            avg_value = non_zero_values.mean() if len(non_zero_values) > 0 else 0
            worksheet.write(avg_row + 1 + i, 0, f"• {platform.split(' ')[0]}:", stat_format)
            worksheet.write(avg_row + 1 + i, 1, f"{avg_value:.2f}", stat_value_format)
            
        # Multi-platform stats
        multi_row = summary_start_row + 16
        worksheet.write(multi_row, 0, "Multi-Platform Statistics:", stat_format)
        
        # Count participants by number of platforms
        platform_counts = df["Active Platforms"].value_counts().sort_index()
        
        for i, (num_platforms, count) in enumerate(platform_counts.items()):
            worksheet.write(multi_row + 1 + i, 0, f"• {num_platforms} Platform(s):", stat_format)
            worksheet.write(multi_row + 1 + i, 1, count, stat_format)
            worksheet.write(multi_row + 1 + i, 2, f"({count/len(df)*100:.1f}%)", stat_format)
            
        # Add charts if requested
        if include_charts:
            # Create separate sheets for different visualizations
            viz_sheet = workbook.add_worksheet('Visualization')
            
            # Add title to visualization sheet
            viz_title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'font_color': '#2E7D32',
            })
            
            viz_sheet.merge_range('A1:O1', f"{title} - Visual Analysis Dashboard", viz_title_format)
            viz_sheet.set_row(0, 30)
            
            # Format column widths
            viz_sheet.set_column('A:A', 15)
            viz_sheet.set_column('B:C', 12)
            viz_sheet.set_column('D:D', 2)  # Spacer column
            viz_sheet.set_column('E:F', 12)
            
            # Add debugging info to help identify potential chart issues
            logger.info("Starting chart generation for Excel file")
            
            # Write platform participation data for charts
            viz_sheet.write('A3', 'Platform', header_format)
            viz_sheet.write('B3', 'Participants', header_format)
            viz_sheet.write('C3', 'Percentage', header_format)
            
            # Calculate platform participation
            platforms = ["CodeChef Score", "CodeForces Score", "GFG Score", "HackerRank Score", "LeetCode Score"]
            platform_handles = ["CodeChef Handle", "CodeForces Handle", "GFG Handle", "HackerRank Handle", "LeetCode Handle"]
            platform_participation = []
            
            for i, platform in enumerate(platforms):
                count = (df[platform] > 0).sum()
                percentage = count / len(df) * 100
                platform_name = platform.split(' ')[0]
                viz_sheet.write(i + 3, 0, platform_name)
                viz_sheet.write(i + 3, 1, count)
                viz_sheet.write(i + 3, 2, percentage)
                platform_participation.append((platform_name, count, percentage))
            
            logger.info(f"Platform participation data: {platform_participation}")
            
            try:
                # 1. Create an improved pie chart showing platform participation
                logger.info("Creating pie chart for platform participation")
                pie_chart = workbook.add_chart({'type': 'pie'})
                pie_chart.add_series({
                    'name': 'Platform Participation',
                    'categories': ['Visualization', 3, 0, 3 + len(platforms) - 1, 0],
                    'values': ['Visualization', 3, 2, 3 + len(platforms) - 1, 2],  # Use percentage values
                    'data_labels': {
                        'percentage': True, 
                        'category': True,
                        'position': 'outside_end',
                        'font': {'bold': True, 'size': 10}
                    },
                    'points': [
                        {'fill': {'color': '#FFC107'}},  # Yellow - CodeChef
                        {'fill': {'color': '#2196F3'}},  # Blue - CodeForces
                        {'fill': {'color': '#4CAF50'}},  # Green - GFG
                        {'fill': {'color': '#F44336'}},  # Red - HackerRank
                        {'fill': {'color': '#9C27B0'}}   # Purple - LeetCode
                    ]
                })
                
                pie_chart.set_title({'name': 'Platform Participation Distribution', 'font': {'size': 14, 'bold': True}})
                pie_chart.set_style(10)
                viz_sheet.insert_chart('A10', pie_chart, {'x_scale': 1.4, 'y_scale': 1.4})
                logger.info("Pie chart created successfully")
                
                # 2. Create a handles verification status chart
                # Count verified vs unverified handles per platform
                logger.info("Creating handle verification bar chart")
                viz_sheet.write('E3', 'Platform', header_format)
                viz_sheet.write('F3', 'Verified', header_format)
                viz_sheet.write('G3', 'Unverified', header_format)
                
                verification_data = []
                for i, platform in enumerate(["CodeChef", "CodeForces", "GFG", "HackerRank", "LeetCode"]):
                    handle_col = f"{platform} Handle"
                    exists_col = f"{platform} Exists"
                    
                    # Count non-empty handles
                    handles_count = (df[handle_col].str.len() > 0).sum()
                    # Count verified handles
                    verified_count = df[exists_col].sum()
                    # Unverified = has handle but not verified
                    unverified_count = handles_count - verified_count
                    
                    viz_sheet.write(i + 3, 4, platform)
                    viz_sheet.write(i + 3, 5, verified_count)
                    viz_sheet.write(i + 3, 6, unverified_count)
                    verification_data.append((platform, verified_count, unverified_count))
                
                logger.info(f"Handle verification data: {verification_data}")
                
                # Create stacked column chart for verification status
                verification_chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
                verification_chart.add_series({
                    'name': 'Verified Handles',
                    'categories': ['Visualization', 3, 4, 3 + len(platforms) - 1, 4],
                    'values': ['Visualization', 3, 5, 3 + len(platforms) - 1, 5],
                    'data_labels': {'value': True},
                    'fill': {'color': '#4CAF50'},  # Green
                })
                
                verification_chart.add_series({
                    'name': 'Unverified Handles',
                    'categories': ['Visualization', 3, 4, 3 + len(platforms) - 1, 4],
                    'values': ['Visualization', 3, 6, 3 + len(platforms) - 1, 6],
                    'data_labels': {'value': True},
                    'fill': {'color': '#F44336'},  # Red
                })
                
                verification_chart.set_title({'name': 'Handle Verification Status', 'font': {'size': 14, 'bold': True}})
                verification_chart.set_y_axis({'name': 'Number of Handles', 'major_gridlines': {'visible': False}})
                verification_chart.set_x_axis({'name': 'Platform'})
                verification_chart.set_legend({'position': 'top'})
                verification_chart.set_style(11)
                viz_sheet.insert_chart('E10', verification_chart, {'x_scale': 1.4, 'y_scale': 1.4})
                logger.info("Verification chart created successfully")
                
                # 3. Create top performers chart
                logger.info("Creating top performers chart")
                if len(df) >= 10:
                    # Create a data table for top 10
                    viz_sheet.write('A30', 'Name', header_format)
                    viz_sheet.write('B30', 'Overall Score', header_format)
                    
                    for i in range(10):
                        name = df.iloc[i]['Name']
                        if len(name) > 20:  # Truncate long names
                            name = name[:18] + '...'
                        viz_sheet.write(30 + i, 0, name)
                        viz_sheet.write(30 + i, 1, df.iloc[i]['Overall Score'])
                    
                    bar_chart = workbook.add_chart({'type': 'bar'})
                    bar_chart.add_series({
                        'name': 'Overall Score',
                        'categories': ['Visualization', 30, 0, 39, 0],
                        'values': ['Visualization', 30, 1, 39, 1],
                        'data_labels': {'value': True, 'position': 'inside_end'},
                        'fill': {'color': '#FFC107'},
                        'border': {'color': '#FF8F00'}
                    })
                    
                    bar_chart.set_title({'name': 'Top 10 Performers', 'font': {'size': 14, 'bold': True}})
                    bar_chart.set_y_axis({'name': 'Student Name', 'major_gridlines': {'visible': False}})
                    bar_chart.set_x_axis({'name': 'Overall Score'})
                    bar_chart.set_legend({'position': 'none'})
                    bar_chart.set_style(11)
                    viz_sheet.insert_chart('A40', bar_chart, {'x_scale': 1.6, 'y_scale': 1.5})
                    logger.info("Top performers chart created successfully")
                
                # 4. Handle vs Score correlation data
                logger.info("Creating platform performance scatter plot")
                viz_sheet.write('E30', 'Platform', header_format)
                viz_sheet.write('F30', 'Handle Count', header_format)
                viz_sheet.write('G30', 'Avg Score', header_format)
                
                platform_performance = []
                for i, platform in enumerate(["CodeChef", "CodeForces", "GFG", "HackerRank", "LeetCode"]):
                    handle_col = f"{platform} Handle"
                    score_col = f"{platform} Score"
                    
                    # Count non-empty handles
                    handles_count = (df[handle_col].str.len() > 0).sum()
                    # Calculate average score for participants with handles
                    avg_score = df[df[handle_col].str.len() > 0][score_col].mean()
                    
                    viz_sheet.write(30 + i, 4, platform)
                    viz_sheet.write(30 + i, 5, handles_count)
                    viz_sheet.write(30 + i, 6, avg_score if not pd.isna(avg_score) else 0)
                    platform_performance.append((platform, handles_count, avg_score if not pd.isna(avg_score) else 0))
                
                logger.info(f"Platform performance data: {platform_performance}")
                
                # Create bubble chart for platform performance 
                bubble_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'bubble'})
                bubble_chart.add_series({
                    'name': 'Platform Performance',
                    'categories': ['Visualization', 30, 5, 34, 5],  # Handle count
                    'values': ['Visualization', 30, 6, 34, 6],      # Average score
                    'bubble_sizes': ['Visualization', 30, 6, 34, 6],  # Use avg score for bubble size
                    'marker': {
                        'type': 'automatic',
                        'size': 15,
                        'border': {'color': 'black'},
                    },
                    'data_labels': {'value': False, 'category': False, 'series_name': False},
                    'points': [
                        {'fill': {'color': '#FFC107'}},  # Yellow - CodeChef
                        {'fill': {'color': '#2196F3'}},  # Blue - CodeForces
                        {'fill': {'color': '#4CAF50'}},  # Green - GFG
                        {'fill': {'color': '#F44336'}},  # Red - HackerRank
                        {'fill': {'color': '#9C27B0'}}   # Purple - LeetCode
                    ]
                })
                
                bubble_chart.set_title({'name': 'Platform Engagement vs Performance', 'font': {'size': 14, 'bold': True}})
                bubble_chart.set_x_axis({'name': 'Number of Users', 'min': 0})
                bubble_chart.set_y_axis({'name': 'Average Score', 'min': 0})
                bubble_chart.set_style(12)
                viz_sheet.insert_chart('E40', bubble_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                logger.info("Platform performance chart created successfully")
                
                # 5. Distribution of scores
                logger.info("Creating score distribution histogram")
                viz_sheet.write('A70', 'Score Range', header_format)
                viz_sheet.write('B70', 'Count', header_format)
                
                # Create score bins
                score_bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
                hist_data = np.histogram(df['Overall Score'], bins=score_bins)
                bin_counts = hist_data[0]
                
                # Write histogram data
                for i, (lower, upper) in enumerate(zip(score_bins[:-1], score_bins[1:])):
                    range_label = f"{lower}-{upper}"
                    viz_sheet.write(71 + i, 0, range_label)
                    viz_sheet.write(71 + i, 1, int(bin_counts[i]))
                
                logger.info(f"Score distribution data: {list(zip(score_bins[:-1], score_bins[1:], bin_counts))}")
                
                # Create column chart for score distribution
                histogram_chart = workbook.add_chart({'type': 'column'})
                histogram_chart.add_series({
                    'name': 'Score Distribution',
                    'categories': ['Visualization', 71, 0, 71 + len(bin_counts) - 1, 0],
                    'values': ['Visualization', 71, 1, 71 + len(bin_counts) - 1, 1],
                    'data_labels': {'value': True},
                    'fill': {'color': '#3F51B5'},
                    'border': {'color': '#303F9F'}
                })
                
                histogram_chart.set_title({'name': 'Distribution of Overall Scores', 'font': {'size': 14, 'bold': True}})
                histogram_chart.set_y_axis({'name': 'Number of Students', 'major_gridlines': {'visible': False}})
                histogram_chart.set_x_axis({'name': 'Score Range'})
                histogram_chart.set_legend({'position': 'none'})
                histogram_chart.set_style(11)
                viz_sheet.insert_chart('A80', histogram_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                logger.info("Score distribution histogram created successfully")
                
                # 6. Platform handles info
                logger.info("Creating platform handle analysis sheet")
                handles_sheet = workbook.add_worksheet('Handle Analysis')
                
                # Add title to handles sheet
                handles_sheet.merge_range('A1:F1', "Platform Handles Analysis", viz_title_format)
                
                # Set column widths
                handles_sheet.set_column('A:A', 8)   # Registration ID
                handles_sheet.set_column('B:B', 20)  # Name
                
                for i, platform in enumerate(["CodeChef", "CodeForces", "GFG", "HackerRank", "LeetCode"]):
                    handles_sheet.set_column(2+i, 2+i, 20)  # Handle columns
                
                # Add headers
                handles_sheet.write('A3', 'ID', header_format)
                handles_sheet.write('B3', 'Name', header_format)
                handles_sheet.write('C3', 'CodeChef', header_format)
                handles_sheet.write('D3', 'CodeForces', header_format)
                handles_sheet.write('E3', 'GFG', header_format)
                handles_sheet.write('F3', 'HackerRank', header_format)
                handles_sheet.write('G3', 'LeetCode', header_format)
                
                # Write handle data with color formatting
                for i, (idx, row) in enumerate(df.iterrows()):
                    handles_sheet.write(i+3, 0, row['Registration ID'])
                    handles_sheet.write(i+3, 1, row['Name'])
                    
                    # Write handles with color formatting based on existence
                    for j, platform in enumerate(["CodeChef", "CodeForces", "GFG", "HackerRank", "LeetCode"]):
                        handle = row[f"{platform} Handle"]
                        exists = row[f"{platform} Exists"]
                        
                        if handle and len(str(handle)) > 0:
                            if exists:
                                handles_sheet.write(i+3, j+2, handle, handle_exists_format)
                            else:
                                handles_sheet.write(i+3, j+2, handle, handle_not_exists_format)
                        else:
                            handles_sheet.write(i+3, j+2, "-")
                
                logger.info("Handle analysis sheet created successfully")
                
            except Exception as e:
                logger.error(f"Error creating charts: {str(e)}", exc_info=True)
                error_sheet = workbook.add_worksheet('Error Info')
                error_sheet.write('A1', f"Error creating charts: {str(e)}")
                error_sheet.write('A2', "Check logs for more details")

        else:
            logger.info("Charts are not included in the Excel file")
        
        # Save the workbook
        try:
            writer.close()
            logger.info(f"Generated Excel leaderboard at: {output_path}")
        except Exception as e:
            logger.error(f"Error saving Excel file: {str(e)}", exc_info=True)
            raise