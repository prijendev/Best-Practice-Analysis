import time
import json
import streamlit as st
from run import run


def filter_json(json_data):
    filtered_json = {}

    for filename, file_data in json_data.items():
        filtered_file_data = {}

        for best_practice, violations in file_data.items():
            if violations:
                filtered_violations = [v for v in violations if v["status"] == "Violated"]

            if filtered_violations:
                filtered_file_data[best_practice] = filtered_violations

        if filtered_file_data:
            filtered_json[filename] = filtered_file_data

    return filtered_json

with st.container():
    st.image(
        "https://miro.medium.com/v2/resize:fit:750/format:webp/1*AvcSX3HOMujgic1RCA6lLQ.png",
        width=150,
    )
    st.title("Best Practices Analyzer")

code_link = st.text_input("Source code link")
best_practice_link = st.text_input("Best practices link")

button_clicked = st.session_state.get("button_clicked", False)

if st.button("Analyze") and not button_clicked:
    if not code_link or not best_practice_link:
        st.error("Please enter both source code link and best practices link.")
    else:
        st.session_state["button_clicked"] = True
        with st.spinner("Analyzing..."):
            data = run(code_link,best_practice_link )
            filtered_data = filter_json(data)
            time.sleep(2)
        st.success("Analysis completed! ✅")
        st.session_state["button_clicked"] = False

        st.write("<br><br>",unsafe_allow_html=True)
        st.write("<h3 style='text-align: center;'>Analysis Report</h3>",unsafe_allow_html=True)

        if filtered_data == {}:
            st.write("No violations found.")

        for key, value in filtered_data.items():
            with st.expander(key):
                for best_practice_name, best_practice_list in value.items():
                    violation_text = ""
                    for best_practice in best_practice_list:
                        status = best_practice["status"]
                        code = best_practice["code"].replace("\n", " <br>")
                        suggestion = best_practice["suggestion"].replace("\n", " <br>")

                        violation_text += f"""
                            <style>
                                .violations-component {{
                                    background-color: #ffffff;
                                    padding: 30px;
                                    border-radius: 5px;
                                    margin-bottom: 20px;
                                    box-shadow: 10px 10px 20px #f2f2f2;
                                    border: 2px solid #f2f2f2;
                                }}
                            </style>
                            <div class="violations-component">
                                <p style="font-weight: bold;">Code:</p>
                                <p style="background-color: #f0eee9;padding: 10px;border-radius: 5px;">{code}</p>
                                <br>
                                <p style="font-weight: bold;">Suggestion:</p> {suggestion}
                            </div>
                """

                    st.markdown(
                        f'''
                            <style>
                                .best-practice-component {{
                                    background-color: #f2f2f2;
                                    padding: 30px;
                                    border-radius: 5px;
                                    margin-bottom: 20px;
                                }}
                            </style>
                            <div class="best-practice-component">
                            <p style="font-weight: bold;">Best practice:</p>{best_practice_name.replace("\n"," <br>")}
                            </div>
                ''',
                        unsafe_allow_html=True,
                    )

                    st.markdown("<p style='font-size: 20;font-weight: bold;color: #db1304;'>Violations: </p>",unsafe_allow_html=True)

                    st.markdown(
                        f"""
                            <style>
                                .data-component {{
                                    background-color: #ffffff;
                                    padding: 30px;
                                    border-radius: 5px;
                                    margin-bottom: 20px;
                                }}
                            </style>
                            <div class="data-component">
                                {violation_text}
                            </div>
                """,
                        unsafe_allow_html=True,
                    )
