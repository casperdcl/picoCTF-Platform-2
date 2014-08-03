renderGroupInformation = _.template($("#group-info-template").remove().text())
renderGroupSelection = _.template($("#group-selection-template").remove().text())

renderTeamSelection = _.template($("#team-selection-template").remove().text())

loadGroupSelection = (groups) ->
  $("#group-selection").html renderGroupSelection({groups: groups})
  $("#group-selector").on "change", (e) ->
    loadGroupInfo()

  selectedGroupName = $("#group-selector").val()

  _.each groups, (group) ->
    if group.name == selectedGroupName
      loadTeamSelection group.gid

loadTeamSelection = (gid) ->
  apiCall "GET", "/api/group/member_information", {gid: gid}
  .done (data) ->
    $("#team-selection").html renderTeamSelection({teams: data.data})
    $(".team-visualization-enabler").on "click", (e) ->
      tid = $(e.target).data("tid")
      console.log(tid)
      apiCall "GET", "/api/team/stats/solved_problems", {tid: tid}
      .done (data) ->
        console.log(data)
    

loadGroupManagement = (groups) ->
  $("#group-management").html renderGroupInformation({data: groups})
  $("#group-request-form").on "submit", groupRequest
  $(".delete-group-span").on "click", (e) ->
    deleteGroup $(e.target).data("group-name")

loadGroupInfo = ->
  apiCall "GET", "/api/group/list", {}
  .done (data) ->
    switch data["status"]
      when 0
        apiNotify(data)
      when 1
        loadGroupManagement data.data
        loadGroupSelection data.data

createGroup = (groupName) ->
  apiCall "POST",  "/api/group/create", {"group-name": groupName}
  .done (data) ->
    apiNotify(data)
    if data['status'] is 1
      loadGroupInfo()

deleteGroup = (groupName) ->
  apiCall "POST", "/api/group/delete", {"group-name": groupName}
  .done (data) ->
    apiNotify(data)
    if data['status'] is 1
      loadGroupInfo()

#Could be simplified without this function
groupRequest = (e) ->
  e.preventDefault()

  groupName = $("#group-name-input").val()
  createGroup groupName

$ ->
  loadGroupInfo()
  return