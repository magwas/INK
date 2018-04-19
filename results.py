#!/usr/bin/python
# coding=utf-8
import csv
import sys

import Szavazas

szavazas = Szavazas.Szavazas()

class Tally:
    def __init__(self):
        self.polls = self.readPolls()
        self.answers = self.readAnswers()
        self.votes, self.byUser = self.readVotes()

    def readAnswers(self):
        answers = {}
        with open('answers.csv') as answersfile:
            reader = csv.DictReader(answersfile, delimiter="\t")
            for row in reader:
                answers[row['polla_aid']] = row
        return answers
        
    def readPolls(self):
        polls = {}
        with open('polls.csv') as pollsfile:
            reader = csv.DictReader(pollsfile, delimiter="\t")
            for row in reader:
                polls[row['pollq_id']] = row
        return polls
        
    def readVotes(self):
        votes = {}
        byUser = {}
        with open('votes.csv') as votesfile:
            reader = csv.DictReader(votesfile, delimiter="\t")
            for row in reader:
                qid = row['qid']
                if not qid in votes:
                    votes[qid] = []
                votes[qid].append(row)
                user_login = row['user_login']
                qid = row['qid']
                aid = row['aid']
                answer = self.answers[aid]['polla_answers']
                if answer in '12345':
                    answer = int(answer)
                if not user_login in byUser:
                    byUser[user_login] = {}
                byUser[user_login][qid]=answer

        return votes,byUser

    def tallyYesNo(self,votes):
        res = {}
        for vote in votes:
            aid = vote['aid']
            if not aid in res:
                res[aid] = 0
            res[aid] = res[aid] +1
        return res
        
    def showResult(self,result, form=" {0}: {1} ({2:.2f}%)\n"):
        resultString = ""
        res = {}
        summa = 0
        for (key,value) in result.items():
            res [self.answers[key]['polla_answers']] = value
            summa += value
        choices = res.keys()
        choices.sort()
        for choice in choices:
            resultString += form.format(choice,res[choice], 100.0*res[choice]/summa)
        return resultString

    def fillBeatTableForUser(self,votes,beatTable):
        for rid1 in beatTable.keys():
            for rid2 in beatTable.keys():
                if (not rid1 in votes) or (not rid2 in votes):
                    break
                if votes[rid1] > votes[rid2]:
                    beatTable[rid1][rid2] += 1
                if votes[rid2] > votes[rid1]:
                    beatTable[rid2][rid1] += 1

    def createSPS(self, candidates):
        sps={}
        for m in candidates:
            sps[m]={}
        return sps

    def computeStrongestPathStrength(self,candidates,d):
        p = self.createSPS(candidates)
        for i in candidates:
            for j in candidates:
                if i != j:
                    if(d[i][j] > d[j][i]):
                        p[i][j] = d[i][j]
                    else:
                        p[i][j] = 0
        for i in candidates:
            for j in candidates:
                if i != j:
                    for k in candidates:
                        if ( i != k ) and ( j != k):
                            p[j][k] = max(p[j][k], min (p[j][i],p[i][k]))
        return p

    def iswinner(self, candidate, candidates,sps):
        for other in candidates:
            if candidate != other and sps[candidate][other] < sps[other][candidate]:
                return False
        return True


    def computeCondorcet(self,beatTable):
        candidates = beatTable.keys()
        sps = self.computeStrongestPathStrength(candidates, beatTable)
        winners = []
        lastWinner = None
        while len(candidates):
            winnersnow = []
            for i in candidates:
                if self.iswinner(i,candidates,sps):
                    beat = ""
                    if lastWinner:
                        beat = "{0}:{1}".format(beatTable[lastWinner][i],beatTable[i][lastWinner])
                    winnersnow.append([i,beat])
                    lastWinner = i
            for candidate in winnersnow:
                candidates.remove(candidate[0])
            winners.append(winnersnow)
        return winners

    def getOrderFor(self,rids):
        votes = []
        beatTable = {}
        for rid in rids:
            votes.append(self.votes[rid])
            beatTable[rid] = {}
            for orid in rids:
                beatTable[rid][orid] = 0
        for uservotes in self.byUser.values():
            self.fillBeatTableForUser(uservotes,beatTable)
        return self.computeCondorcet(beatTable)


    def showCondorcetresult(self,weekorder):
        res = ""
        order = 1
        for place in weekorder:
            res += " {0}. hely:\n".format(order)
            order += 1
            for candidate,beat in place:
                qid = szavazas.getPollForOrder(candidate)
                question = self.polls[qid]['pollq_question']
                res += "  {0} ({1})\n".format(question, beat)
        return res

    def tally(self):
        allrids = []
        for week in range(1,8):
            weekRids = []
            for szav in range(1,8):
                (qid, rid) =  szavazas.getPoll(week,szav)
                weekRids.append(rid)
                allrids.append(rid)
                print "%s. hét %s.szavazás: %s"%(week,szav,self.polls[qid]['pollq_question'])
                result = self.tallyYesNo(self.votes[qid])
                print self.showResult(result)
            weekorder = self.getOrderFor(weekRids)
            print " kérdések fontossági sorrendje a {0}. héten:".format(week)
            print self.showCondorcetresult(weekorder)
        allorder = self.getOrderFor(allrids)
        print " kérdések fontossági sorrendje összesen:"
        print self.showCondorcetresult(allorder)
Tally().tally()
